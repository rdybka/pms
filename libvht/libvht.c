/* libvht.c - Valhalla Tracker (libvht)
 *
 * Copyright (C) 2020 Remigiusz Dybka - remigiusz.dybka@gmail.com
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <stdio.h>
#include <string.h>
#include "midi_client.h"
#include "jack_process.h"

#include "module.h"
#include "libvht.h"

// getters/setters and global stuff

midi_client *module_get_midi_client(module *mod) {
	return mod->clt;
}

char *get_midi_error(module *mod) {
	return mod->clt->error;
}

int module_get_max_ports(module *mod) {
	return MIDI_CLIENT_MAX_PORTS;
}

float module_get_bpm(module *mod) {
	return mod->bpm;
}

int get_max_ports(module *mod) {
	return MIDI_CLIENT_MAX_PORTS;
}

void module_set_bpm(module *mod, float bpm) {
	mod->bpm = bpm;
}

void module_play(module *mod, int play) {
	mod->playing = play;
	if (play == 0)
		module_mute(mod);
}

int module_is_playing(module *mod) {
	return mod->playing;
}

void module_record(module *mod, int rec) {
	mod->recording = rec;
}

int module_is_recording(module *mod) {
	return mod->recording;
}

int module_get_rpb(module *mod) {
	return mod->rpb;
}

void module_set_rpb(module *mod, int v) {
	module_excl_in(mod);
	mod->rpb = v;
	module_excl_out(mod);
}

void module_reset(module *mod) {
	mod->zero_time = 0;
	for (int s = 0; s < mod->nseq; s++) {
		mod->seq[0]->pos = 0;
		for (int t = 0; t < mod->seq[0]->ntrk; t++)
			track_reset(mod->seq[0]->trk[t]);
	}
}

int module_get_nseq(module *mod) {
	return mod->nseq;
}

sequence *module_get_seq(module *mod, int n) {
	return mod->seq[n];
}

int module_get_curr_seq(module *mod) {
	return mod->curr_seq;
}

void module_set_curr_seq(module *mod, int s) {
	mod->curr_seq = s;
}

int module_get_ctrlpr(module *mod) {
	return mod->ctrlpr;
}

void module_set_ctrlpr(module *mod, int ctrlpr) {
	mod->ctrlpr = ctrlpr;
}

int sequence_get_ntrk(sequence *seq) {
	return seq->ntrk;
}

int sequence_get_length(sequence *seq) {
	return seq->length;
}

int sequence_get_index(sequence *seq) {
	return seq->index;
}

int sequence_get_max_length(void) {
	return SEQUENCE_MAX_LENGTH;
}

track *sequence_get_trk(sequence *seq, int n) {
	return seq->trk[n];
}

row *track_get_row_ptr(track *trk, int c, int r) {
	return &trk->rows[c][r];
}

ctrlrow *track_get_ctrlrow_ptr(track *trk, int c, int r) {
	return &trk->crows[c][r];
}

int track_get_length(track *trk) {
	return trk->nrows;
}

int track_get_ncols(track *trk) {
	return trk->ncols;
}

int track_get_port(track *trk) {
	return trk->port;
}

int track_get_channel(track *trk) {
	return trk->channel;
}

int track_get_index(track *trk) {
	return trk->index;
}

int track_get_nrows(track *trk) {
	return trk->nrows;
}

int track_get_nsrows(track *trk) {
	return trk->nsrows;
}

int track_get_playing(track *trk) {
	return trk->playing;
}

int track_get_nctrl(track *trk) {
	return trk->nctrl;
}

int track_get_ctrlpr(track *trk) {
	return trk->ctrlpr;
}

double track_get_pos(track *trk) {
	return trk->pos;
}

void track_set_port(track *trk, int n) {
	trk->port = n;
}

void track_set_channel(track *trk, int n) {
	trk->channel = n;
}

void track_set_program(track *trk, int p) {
	trk->prog = p;
	trk->prog_sent = 0;
}

void track_set_bank(track *trk, int msb, int lsb) {
	trk->bank_msb = msb;
	trk->bank_lsb = lsb;
}

char *track_get_program(track *trk) {
	static char rc[256];
	sprintf(rc, "[%3d, %3d, %3d]", trk->bank_msb, trk->bank_lsb, trk->prog);
	return rc;
}

char *track_get_qc(track *trk) {
	static char rc[256];
	sprintf(rc, "[%3d, %3d, %3d, %3d]", trk->qc1_ctrl, trk->qc1_val, trk->qc2_ctrl, trk->qc2_val);
	return rc;
}

void track_set_qc1(track *trk, int ctrl, int val) {
	trk->qc1_ctrl = ctrl;
	trk->qc1_val = val;
}

void track_set_qc2(track *trk, int ctrl, int val) {
	trk->qc2_ctrl = ctrl;
	trk->qc2_val = val;
}

void track_set_loop(track *trk, int v) {
	trk->loop = v;
}

int track_get_loop(track *trk) {
	return trk->loop;
}

int track_get_indicators(track *trk) {
	return trk->indicators;
}

void track_set_indicators(track *trk, int i) {
	trk->indicators = i;
}

void track_clear_indicators(track *trk) {
	trk->indicators = 0;
}


void sequence_set_trg_quantise(sequence *seq, int v) {
	seq->trg_quantise = v;
}

int sequence_get_trg_quantise(sequence *seq) {
	return seq->trg_quantise;
}

void sequence_set_trg_playmode(sequence *seq, int v) {
	seq->trg_playmode = v;
}

int sequence_get_trg_playmode(sequence *seq) {
	return seq->trg_playmode;
}

void sequence_set_trig(sequence *seq, int t, int tp, int ch, int nt) {
	if ((t > 2) || (t < 0))
		return;
	seq->triggers[t].type = tp;
	seq->triggers[t].channel = ch;
	seq->triggers[t].note = nt;
}

char *sequence_get_trig(sequence *seq, int t) {
	static char rc[256];

	if ((t > 2) || (t < 0))
		return "[0,0,0]";

	sprintf(rc, "[%3d, %3d, %3d]", seq->triggers[t].type, seq->triggers[t].channel, seq->triggers[t].note);
	return rc;
}


double sequence_get_pos(sequence *seq) {
	return seq->pos;
}

void track_set_playing(track *trk, int p) {
	trk->playing = p;
	if (p == 0) {
		track_kill_notes(trk);
	}
}

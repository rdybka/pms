/* module.c - Valhalla Tracker (libvht)
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
#include <math.h>
#include <pthread.h>
#include "module.h"
#include "midi_client.h"
#include "track.h"
#include "midi_event.h"

struct rec_update_t rec_update[MIDI_EVT_BUFFER_LENGTH];
int cur_rec_update;

int lastsec;

void module_excl_in(module *mod) {
	pthread_mutex_lock(&mod->excl);
}

void module_excl_out(module *mod) {
	pthread_mutex_unlock(&mod->excl);
}

int trg_equal(trigger *trg, midi_event *mev) {
	int eq = 0;
	if ((mev->channel == trg->channel) && \
	        (mev->type == trg->type) && \
	        (mev->note == trg->note))
		eq = 1;

	return eq;
}

// the god-function
void module_advance(module *mod, jack_nframes_t curr_frames) {
	if (mod->nseq == 0) {
		return;
	}

	module_excl_in(mod);
	midi_buffer_clear(mod->clt);

	double time = (curr_frames - mod->zero_time) / (double)mod->clt->jack_sample_rate;
	double row_length = 60.0 / (double)mod->bpm;
	double period = ((double)mod->clt->jack_buffer_size / (double)mod->clt->jack_sample_rate) / row_length;

	// are we muting after stop?
	if (!mod->playing) {
		if (mod->mute) {
			for (int t = 0; t < mod->seq[mod->curr_seq]->ntrk; t++)
				track_kill_notes(mod->seq[mod->curr_seq]->trk[t]);

			mod->mute = 0;
		}
	} else {
		mod->sec = time;
		mod->min = mod->sec / 60;
		mod->sec -= (mod->min * 60);

		mod->ms = (time - floorf(time)) * 1000;
	}

	if (mod->zero_time == 0) {
		mod->zero_time = curr_frames;
	}

// handle input from MIDI
	void *inp = jack_port_get_buffer(mod->clt->jack_input_port, mod->clt->jack_buffer_size);

	jack_nframes_t ninp;
	jack_midi_event_t evt;

	ninp = jack_midi_get_event_count(inp);

	int empty = 0;

	for (jack_nframes_t n = 0; (n < ninp) && !empty; n++) {
		empty = jack_midi_event_get(&evt, inp, n);
		if (!empty) {
			midi_event mev = midi_decode_event(evt.buffer, evt.size);
			mev.time = evt.time;

			if (!mod->recording) {
				midi_buffer_add(mod->clt, mod->clt->default_midi_port, mev);
			}

			// handle triggers
			for (int s = 0; s < mod->nseq; s++) {
				if (mev.velocity > 0) {
					if ((mod->seq[s]->triggers[0].type) && trg_equal(&mod->seq[s]->triggers[0], &mev)) {
						sequence_trigger_mute(mod->seq[s]);
					}

					if ((mod->seq[s]->triggers[1].type) && trg_equal(&mod->seq[s]->triggers[1], &mev)) {
						sequence_trigger_cue(mod->seq[s]);
					}

					if ((mod->seq[s]->triggers[2].type) && trg_equal(&mod->seq[s]->triggers[2], &mev)) {
						sequence_trigger_play_on(mod->seq[s]);
					}
				}

				trigger trg = mod->seq[s]->triggers[2];

				if ((mod->seq[s]->triggers[2].type == note_on) && \
				        (mev.channel == trg.channel) && \
				        (mev.type == note_off) && \
				        (mev.note == trg.note)) {
					sequence_trigger_play_off(mod->seq[s]);
				}

				if ((mod->seq[s]->triggers[2].type == control_change) && \
				        (mev.channel == trg.channel) && \
				        (mev.type == trg.type) && \
				        (mev.note == trg.note) && \
				        (mev.velocity == 0)) {
					sequence_trigger_play_off(mod->seq[s]);
				}
			}

			midi_in_buffer_add(mod->clt, mev);

			int ignore = 0;

			midi_ignore_buff_excl_in(mod->clt);
			for (int f = 0; f < mod->clt->curr_midi_ignore_event; f++) {
				midi_event ignev = mod->clt->midi_ignore_buffer[f];
				if (ignev.channel == mev.channel)
					if (ignev.type == mev.type)
						if (ignev.note == mev.note)
							ignore = 1;
			}

			if (mod->recording && !ignore) {
				sequence_handle_record(mod, mod->seq[mod->curr_seq], mev);
			}

			for (int t = 0; t < mod->seq[mod->curr_seq]->ntrk; t++) {
				if (mod->seq[mod->curr_seq]->trk[t]->channel == mev.channel) {
					mod->seq[mod->curr_seq]->trk[t]->indicators |= 1;
				}
			}

			midi_ignore_buff_excl_out(mod->clt);
		}
	}

	if (mod->playing) {
		if (mod->play_mode == 0) {
			for (int s = 0; s < mod->nseq; s++) {
				sequence *seq = mod->seq[s];
				if (seq->lost) {
					seq->pos = fmod(mod->song_pos * seq->rpb, seq->length);

					for (int t = 0; t < seq->ntrk; t++) {
						seq->trk[t]->pos = seq->pos;
					}
					seq->lost = 0;
				}

				sequence_advance(seq, period * seq->rpb, mod->clt->jack_buffer_size);
			}
			mod->song_pos += period;
		} else {
			timeline_advance(mod->tline, period);

		}
	}

	//printf("time: %02d:%02d:%03d %3.5f %d\n", module.min, module.sec, module.ms, period, module.bpm);
	module_excl_out(mod);
}

module *module_new() {
	module *mod = malloc(sizeof(module));

	mod->bpm = 120;
	mod->nseq = 0;
	mod->curr_seq = 0;
	mod->playing = 0;
	mod->recording = 0;
	mod->zero_time = 0;
	mod->song_pos = 0.0;
	mod->mute = 0;
	mod->ctrlpr = DEFAULT_CTRLPR;
	mod->cur_rec_update = 0;
	mod->tline = timeline_new();
	mod->seq = malloc(sizeof(sequence *));
	pthread_mutex_init(&mod->excl, NULL);
	mod->clt = midi_client_new(mod);
	mod->play_mode = 0;
	return mod;
}

void module_mute(module *mod) {
	mod->mute = 1;
}

void module_reset(module *mod) {
	mod->zero_time = 0;
	mod->song_pos = 0;
	mod->min = mod->sec = mod->ms = 0;
	for (int s = 0; s < mod->nseq; s++) {
		mod->seq[s]->pos = 0;
		//mod->seq[s]->lost = 1;
		for (int t = 0; t < mod->seq[s]->ntrk; t++)
			track_reset(mod->seq[s]->trk[t]);
	}
}

void module_seqs_reindex(module *mod) {
	for (int s = 0; s < mod->nseq; s++) {
		mod->seq[s]->index = s;
	}
}

void module_free(module *mod) {
	midi_stop(mod->clt);
	for (int s = 0; s < mod->nseq; s++)
		sequence_free(mod->seq[s]);

	free(mod->seq);
	timeline_free(mod->tline);
	pthread_mutex_destroy(&mod->excl);
	free(mod);
}

void module_dump_notes(module *mod, int n) {
	mod->clt->dump_notes = n;
}

void module_add_sequence(module *mod, sequence *seq) {
	module_excl_in(mod);

	double pos = 0;
	if (mod->nseq) {
		pos = mod->seq[0]->pos;
	}

	mod->seq = realloc(mod->seq, sizeof(sequence *) * (mod->nseq + 1));
	mod->seq[mod->nseq++] = seq;
	seq->mod_excl = &mod->excl;
	seq->clt = mod->clt;

	if (pos > 0.0) {
		seq->pos = pos;
		for (int t = 0; t < seq->ntrk; t++) {
			track_wind(seq->trk[t], pos);
		}
	}

	module_seqs_reindex(mod);
	module_excl_out(mod);
}

void module_del_sequence(module *mod, int s) {
	if (s == -1)
		s = mod->nseq - 1;

	if ((s < 0) || (s >= mod->nseq))
		return;

	module_excl_in(mod);

	sequence_free(mod->seq[s]);

	for (int i = s; i < mod->nseq - 1; i++) {
		mod->seq[i] = mod->seq[i + 1];
	}

	mod->nseq--;

	if (mod->nseq == 0) {
		free(mod->seq);
		mod->seq = 0;
	} else {
		mod->seq = realloc(mod->seq, sizeof(sequence *) * mod->nseq);
	}

	module_seqs_reindex(mod);
	module_excl_out(mod);
}

void module_swap_sequence(module *mod, int s1, int s2) {
	if ((s1 < 0) || (s1 >= mod->nseq))
		return;

	if ((s2 < 0) || (s2 >= mod->nseq))
		return;

	if (s1 == s2)
		return;

	module_excl_in(mod);

	sequence *s3 = mod->seq[s1];
	mod->seq[s1] = mod->seq[s2];
	mod->seq[s2] = s3;

	module_seqs_reindex(mod);
	module_excl_out(mod);
}

timeline *module_get_timeline(module *mod) {
	return mod->tline;
}

char *module_get_time(module *mod) {
	static char buff[256];
	sprintf(buff, "%02d:%02d:%03d", mod->min, mod->sec, mod->ms);
	return buff;
}

double module_get_jack_pos(module *mod) {
	double row_length = 60.0 / ((double)mod->bpm);
	return (mod->song_pos + (((jack_frame_time(mod->clt->jack_client) - mod->clt->jack_last_frame) / (double)mod->clt->jack_sample_rate) / row_length));
}

void module_synch_output_ports(module *mod) {
	midi_buff_excl_in(mod->clt);

	for (int p = 0; p < MIDI_CLIENT_MAX_PORTS; p++) {
		mod->clt->ports_to_open[p] = 0;
		if (mod->clt->curr_midi_queue_event[p])
			mod->clt->ports_to_open[p] = 1;
	}

	mod->clt->ports_to_open[mod->clt->default_midi_port] = 1;

	for (int s = 0; s < mod->nseq; s++)
		for (int t = 0; t < mod->seq[s]->ntrk; t++)
			mod->clt->ports_to_open[mod->seq[s]->trk[t]->port] = 1;

	midi_buff_excl_out(mod->clt);
}

void module_set_play_mode(module *mod, int m) {
	if (!m) {
		mod->play_mode = 0;
	} else {
		mod->play_mode = 1;
	}
}

int module_get_play_mode(module *mod) {
	return mod->play_mode;
}
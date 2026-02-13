/*
 * midimech-vport: Zero-overhead virtual MIDI cable for ALSA sequencer.
 *
 * Creates a single ALSA sequencer port named "midimech" that acts as a
 * pass-through: any MIDI written to it is forwarded to all subscribers.
 *
 * This replaces the Python rtmidi2 callback approach, eliminating GIL
 * overhead and providing jitter-free MIDI forwarding at any buffer size.
 *
 * Equivalent to loopMIDI on Windows.
 */

#include <alsa/asoundlib.h>
#include <signal.h>
#include <stdio.h>

static volatile int running = 1;

static void on_signal(int sig) {
    (void)sig;
    running = 0;
}

int main(void) {
    snd_seq_t *seq;
    int err;

    err = snd_seq_open(&seq, "default", SND_SEQ_OPEN_DUPLEX, 0);
    if (err < 0) {
        fprintf(stderr, "Cannot open ALSA sequencer: %s\n", snd_strerror(err));
        return 1;
    }

    snd_seq_set_client_name(seq, "midimech");

    /* Create a single port with both read and write capabilities.
     * - WRITE + SUBS_WRITE: midimech.py can send MIDI here
     * - READ + SUBS_READ: SurgeXT (or any synth) can subscribe to receive MIDI
     */
    int port = snd_seq_create_simple_port(seq, "midimech",
        SND_SEQ_PORT_CAP_WRITE | SND_SEQ_PORT_CAP_SUBS_WRITE |
        SND_SEQ_PORT_CAP_READ  | SND_SEQ_PORT_CAP_SUBS_READ,
        SND_SEQ_PORT_TYPE_MIDI_GENERIC | SND_SEQ_PORT_TYPE_APPLICATION);

    if (port < 0) {
        fprintf(stderr, "Cannot create port: %s\n", snd_strerror(port));
        snd_seq_close(seq);
        return 1;
    }

    fprintf(stderr, "[midimech-vport] Virtual MIDI cable 'midimech' ready (port %d)\n", port);

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);

    /* Event loop: read incoming MIDI events, forward to all subscribers */
    snd_seq_event_t *ev;
    while (running) {
        err = snd_seq_event_input(seq, &ev);
        if (err < 0) {
            if (err == -EAGAIN) continue;
            break;
        }

        snd_seq_ev_set_source(ev, port);
        snd_seq_ev_set_subs(ev);
        snd_seq_ev_set_direct(ev);
        snd_seq_event_output_direct(seq, ev);
    }

    snd_seq_close(seq);
    return 0;
}

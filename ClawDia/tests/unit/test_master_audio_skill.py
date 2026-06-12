import sys, os, json
from pathlib import Path
import numpy as np

SRC = Path(__file__).parents[2] / "src"
sys.path.insert(0, str(SRC))

def test_imports():
    import soundfile as sf
    assert sf is not None
    import librosa
    assert librosa is not None
    import sounddevice as sd
    assert sd is not None
    import speech_recognition as sr
    assert sr is not None
    import onnxruntime
    assert onnxruntime is not None
    from scipy import signal, io
    assert signal is not None
    print("  [PASS] All audio imports resolved")

def test_module_functions():
    from tools.master_skills.audioSkill import (
        load_audio, save_audio, generate_tone, audio_duration,
        freq_to_midi, midi_to_freq, midi_to_name, apply_crossfade,
        change_volume, time_stretch, pitch_shift
    )
    tone = generate_tone(440, 0.5, 22050)
    assert len(tone) > 0
    assert tone.dtype == np.float64
    assert abs(freq_to_midi(440) - 69) < 0.01
    assert abs(midi_to_freq(69) - 440) < 0.01
    assert midi_to_name(60) == "C4"
    assert midi_to_name(0) == "REST"
    result = apply_crossfade(tone, 22050, 50)
    assert len(result) == len(tone)
    louder = change_volume(tone, 6)
    assert np.abs(louder).mean() > np.abs(tone).mean()
    stretched = time_stretch(tone, 22050, 2.0)
    assert len(stretched) < len(tone)
    shifted = pitch_shift(tone, 22050, 2)
    assert len(shifted) == len(tone)
    print("  [PASS] Module-level functions (generate_tone, freq_to_midi, etc.)")

def test_audio_format_enum():
    from tools.master_skills.audioSkill import AudioFormat
    assert AudioFormat.WAV.value == "wav"
    assert AudioFormat.MP3.value == "mp3"
    assert AudioFormat.FLAC.value == "flac"
    assert len(AudioFormat) == 6
    print("  [PASS] AudioFormat enum")

def test_cancel_flags():
    from tools.master_skills.audioSkill import CANCEL, CancelFlags
    assert isinstance(CANCEL, CancelFlags)
    cf = CancelFlags()
    ev = cf.get("test")
    assert not ev.is_set()
    cf.cancel("test")
    assert ev.is_set()
    cf.reset("test")
    assert not ev.is_set()
    print("  [PASS] CancelFlags")

def test_pitch_detectors():
    from tools.master_skills.audioSkill import (
        AutoCorrelationPitchDetector, PitchTracker
    )
    sr = 22050
    y = np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, int(sr * 0.5)))
    apd = AutoCorrelationPitchDetector()
    pitches = apd.detect(y, sr)
    assert len(pitches) > 0
    tracker = PitchTracker("autocorrelation")
    pitches2 = tracker.track(y, sr)
    assert len(pitches2) > 0
    print("  [PASS] Pitch detectors (AutoCorrelationPitchDetector, PitchTracker)")

def test_midi_events_and_scales():
    from tools.master_skills.audioSkill import MIDIEvent, AeolianScaleMatrix, NOTE_NAMES
    ev = MIDIEvent(note=60, velocity=100, start=0.0, duration=0.5)
    assert ev.note == 60
    assert len(NOTE_NAMES) == 12
    scale = AeolianScaleMatrix(root=60, mode="aeolian")
    assert scale.get_note(0) == 60
    assert scale.get_note(1) == 62
    print("  [PASS] MIDIEvent, AeolianScaleMatrix, NOTE_NAMES")

def test_markov_and_rhyme():
    from tools.master_skills.audioSkill import (
        MarkovMelodyGenerator, MarkovGeneticLyricEngine,
        RhymeScorer, RhymeFlowSuggester, LyricEnhancer
    )
    mg = MarkovMelodyGenerator(order=2)
    mg.train([60, 62, 64, 65, 64, 62])
    notes = mg.generate(10)
    assert len(notes) == 10
    engine = MarkovGeneticLyricEngine(order=2)
    engine.train(["hello world this is a test"])
    words = engine.generate(seed=["hello", "world"])
    assert len(words) >= 2
    scorer = RhymeScorer()
    score = scorer.score("time", "rhyme")
    assert isinstance(score, float)
    suggester = RhymeFlowSuggester()
    suggestions = suggester.suggest("love", ["dove", "heart", "above"])
    assert len(suggestions) > 0
    enhancer = LyricEnhancer()
    enhanced = enhancer.enhance("love is strong")
    assert "devotion" in enhanced or "unbreakable" in enhanced
    print("  [PASS] Markov chains, rhyme scoring, lyric enhancement")

def test_phoneme_matcher():
    from tools.master_skills.audioSkill import PhonemeMatcher
    pm = PhonemeMatcher()
    score = pm.match("test", ["t", "e", "s", "t"])
    assert score > 0
    score2 = pm.match("hello", ["z", "z", "z"])
    assert score2 == 0.0
    print("  [PASS] PhonemeMatcher")

def test_syllable_segmenter():
    from tools.master_skills.audioSkill import SyllableSegmenter
    seg = SyllableSegmenter()
    nodes = seg.segment("hello world")
    assert len(nodes) >= 2
    assert nodes[0].text
    assert nodes[0].duration > 0
    print("  [PASS] SyllableSegmenter")

def test_tick_quantizer():
    from tools.master_skills.audioSkill import TickQuantizer
    tq = TickQuantizer(ticks_per_beat=480, bpm=120)
    ticks = tq.quantize(1.0)
    assert ticks == 960
    print("  [PASS] TickQuantizer")

def test_dtw_aligner():
    from tools.master_skills.audioSkill import DTWAligner, ForcedAligner
    aligner = DTWAligner()
    fa = ForcedAligner()
    print("  [PASS] DTWAligner, ForcedAligner classes loadable")

def test_cadence_enforcer():
    from tools.master_skills.audioSkill import CadenceEnforcer
    ce = CadenceEnforcer()
    result = ce.enforce([60, 62, 64, 65], [60, 62, 64, 65, 67, 69, 71])
    assert len(result) > 0
    assert result[-1] == 60
    print("  [PASS] CadenceEnforcer")

def test_drum_and_chord_generation():
    from tools.master_skills.audioSkill import generate_drum_track, generate_chord_track
    drums = generate_drum_track(bpm=120, pattern="four_on_floor", duration_bars=2, sr=22050)
    assert len(drums) > 0
    chords = generate_chord_track(scale="major", key_root=60, bpm=120, duration_bars=2, sr=22050)
    assert len(chords) > 0
    print("  [PASS] Drum / chord generation")

def test_session_state():
    import tempfile
    from tools.master_skills.audioSkill import SessionState
    with tempfile.TemporaryDirectory() as td:
        state = SessionState(Path(td) / "state.json")
        state.set("key1", "value1")
        state.set("key2", 42)
        state.save()
        state2 = SessionState(Path(td) / "state.json")
        state2.load()
        assert state2.get("key1") == "value1"
        assert state2.get("key2") == 42
        assert state2.get("nonexistent", "default") == "default"
    print("  [PASS] SessionState (save/load)")

def test_batch_processor():
    from tools.master_skills.audioSkill import BatchProcessor
    bp = BatchProcessor(max_workers=2)
    assert bp.max_workers == 2
    print("  [PASS] BatchProcessor")

def test_voice_adapter():
    from tools.master_skills.audioSkill import VoiceAdapter
    va = VoiceAdapter(embedding_dim=128)
    assert va.embedding_dim == 128
    src = [np.random.randn(128) for _ in range(3)]
    tgt = [np.random.randn(128) for _ in range(3)]
    va.train(src, tgt)
    assert va.adapter is not None
    result = va.apply(np.random.randn(128))
    assert result.shape == (128,)
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "adapter.npz"
        va.save(p)
        va2 = VoiceAdapter()
        va2.load(p)
        assert va2.adapter is not None
    print("  [PASS] VoiceAdapter (train/apply/save/load)")

def test_audio_class_definition():
    from tools.master_skills.audioSkill import (
        AudioSkill, DemucsSeparator, RemixPipeline,
        VoskTranscriber, MusicVideoGenerator
    )
    assert AudioSkill is not None
    assert DemucsSeparator is not None
    assert RemixPipeline is not None
    assert VoskTranscriber is not None
    assert MusicVideoGenerator is not None
    print("  [PASS] Core class definitions loadable")

def test_audio_skill_instantiation():
    from tools.master_skills.audioSkill import AudioSkill
    skill = AudioSkill()
    assert skill is not None
    caps = skill.get_capabilities()
    assert len(caps) == 24
    assert "stem_separation" in caps
    assert "transcription" in caps
    assert "voice_commands" in caps
    print("  [PASS] AudioSkill instantiation + get_capabilities()")

def test_model_inference_class():
    from tools.master_skills.audioSkill import ModelInference, ModelTrainer
    mi = ModelInference({"model_path": "nonexistent.onnx"})
    assert mi is not None
    assert mi.classes is not None
    mt = ModelTrainer()
    assert mt is not None
    print("  [PASS] ModelInference, ModelTrainer instantiation")

def test_audio_processor_class():
    from tools.master_skills.audioSkill import AudioProcessor
    cfg = {"sample_rate": 16000}
    ap = AudioProcessor(cfg)
    assert ap.sample_rate == 16000
    dummy = np.random.randn(16000).astype(np.float32)
    anti = ap.generate_anti_noise(dummy)
    assert anti.shape == dummy.shape
    profile = np.random.randn(16000).astype(np.float32)
    filtered = ap.adaptive_filter(dummy, noise_profile=profile)
    assert filtered.shape == dummy.shape
    print("  [PASS] AudioProcessor (generate_anti_noise, adaptive_filter)")

def test_voice_commands_class():
    from tools.master_skills.audioSkill import VoiceCommands
    vc = VoiceCommands({"wake_word": "hey mute"})
    assert vc.wake_word == "hey mute"
    cmd = vc._match_command("mute")
    assert cmd == "mute"
    cmd2 = vc._match_command("unmute")
    assert cmd2 == "unmute"
    assert vc._fuzzy_match("mute", "mute", 0.7)
    assert vc._fuzzy_match("mutee", "mute", 0.7)
    assert not vc._fuzzy_match("xyz", "volume up", 0.7)
    print("  [PASS] VoiceCommands (wake word, matching)")

def test_save_load_audio_roundtrip():
    import tempfile
    from tools.master_skills.audioSkill import save_audio, load_audio, generate_tone
    tone = generate_tone(440, 0.5, 22050)
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.wav"
        save_audio(p, tone, 22050)
        assert p.exists()
        data, sr = load_audio(p)
        assert sr == 22050
        assert len(data) > 0
    print("  [PASS] Audio save/load roundtrip")

def test_wav_to_abc():
    from tools.master_skills.audioSkill import wav_to_abc
    import tempfile
    from tools.master_skills.audioSkill import save_audio, generate_tone
    tone = generate_tone(440, 0.5, 22050)
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.wav"
        save_audio(p, tone, 22050)
        abc = wav_to_abc(p)
        assert abc.startswith("X:1")
        assert "K:C" in abc
    print("  [PASS] wav_to_abc")


if __name__ == "__main__":
    tests = [
        ("imports", test_imports),
        ("functions", test_module_functions),
        ("AudioFormat enum", test_audio_format_enum),
        ("CancelFlags", test_cancel_flags),
        ("pitch detectors", test_pitch_detectors),
        ("MIDI/scale", test_midi_events_and_scales),
        ("Markov/rhyme", test_markov_and_rhyme),
        ("PhonemeMatcher", test_phoneme_matcher),
        ("SyllableSegmenter", test_syllable_segmenter),
        ("TickQuantizer", test_tick_quantizer),
        ("DTWAligner", test_dtw_aligner),
        ("CadenceEnforcer", test_cadence_enforcer),
        ("drum/chord", test_drum_and_chord_generation),
        ("SessionState", test_session_state),
        ("BatchProcessor", test_batch_processor),
        ("VoiceAdapter", test_voice_adapter),
        ("class defs", test_audio_class_definition),
        ("AudioSkill", test_audio_skill_instantiation),
        ("ModelInference", test_model_inference_class),
        ("AudioProcessor", test_audio_processor_class),
        ("VoiceCommands", test_voice_commands_class),
        ("save/load", test_save_load_audio_roundtrip),
        ("wav_to_abc", test_wav_to_abc),
    ]
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    sys.exit(0 if failed == 0 else 1)

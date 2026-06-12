# VAN_Engine — Project Structure

├── api/
│   └── server.py
├── artifacts/
│   └── contributions/
│       └── 2026-06-09_deepseek-webui_red-team-roadmap-analysis.md
├── bridges/
│   └── gemini_bridge.py
├── catalog/
│   ├── bingx-massofman/
│   │   └── bipolar.json
│   ├── cryptic-wisdom/
│   │   ├── bottled-up.json
│   │   ├── cryptic-wisdom-all-lyrics.json
│   │   └── hindsight-album.json
│   ├── ekoh/
│   │   └── d4rk-side.json
│   ├── gawne/
│   │   ├── cardiac-arrest.json
│   │   └── forgive-me.json
│   └── seppi-gawne/
│       └── runaway.json
├── ClawDia/
│   ├── config/
│   │   └── Settings.json
│   ├── plugins/
│   │   └── example_plugin/
│   │       └── __init__.py
│   ├── skills/
│   │   ├── audio/
│   │   │   └── __init__.py
│   │   ├── video/
│   │   │   └── __init__.py
│   │   ├── vision/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   ├── src/
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── loop.py
│   │   │   ├── prompts.py
│   │   │   ├── skill.py
│   │   │   └── tools.py
│   │   ├── artifacts/
│   │   │   ├── humor/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ascii_collection.py
│   │   │   │   ├── detector_state.json
│   │   │   │   ├── humor_seed_lexicon.json
│   │   │   │   ├── meme_feedback.json
│   │   │   │   ├── meme_forge_arc_lade.py
│   │   │   │   └── README_meme_forge.md
│   │   │   └── vessel_manifesto.md
│   │   ├── core/
│   │   │   ├── memory/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── episodic.py
│   │   │   │   ├── hybrid.py
│   │   │   │   └── semantic.py
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   └── logger.py
│   │   ├── harness/
│   │   │   ├── __init__.py
│   │   │   └── cli.py
│   │   ├── plugin/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── lifecycle.py
│   │   │   ├── loader.py
│   │   │   ├── registry.py
│   │   │   └── sandbox.py
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── chunking.py
│   │   │   ├── cli.py
│   │   │   ├── context.py
│   │   │   ├── embedding.py
│   │   │   ├── engine.py
│   │   │   ├── ingestion.py
│   │   │   └── store.py
│   │   ├── scripts/
│   │   │   ├── __init__.py
│   │   │   ├── migrate_replay_log.py
│   │   │   ├── skill_cli.py
│   │   │   └── sovereign_code_guardian.py
│   │   ├── server/
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py
│   │   │   │   ├── hooks.py
│   │   │   │   ├── memory.py
│   │   │   │   ├── rag.py
│   │   │   │   ├── skills.py
│   │   │   │   └── voice.py
│   │   │   ├── static/
│   │   │   │   ├── __init__.py
│   │   │   │   └── dashboard.html
│   │   │   ├── __init__.py
│   │   │   ├── _launch.py
│   │   │   ├── app.py
│   │   │   └── run.py
│   │   ├── skills/
│   │   │   ├── comic_output/
│   │   │   │   ├── midnight_rage_volume5.html
│   │   │   │   └── midnight_rage_volume5_ascii.html
│   │   │   ├── generated/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── query_filesystem_count.py
│   │   │   │   ├── transform_filesystem_convert.py
│   │   │   │   ├── transform_unknown_convert_Skills.md
│   │   │   │   └── unknown_filesystem_unknown.py
│   │   │   ├── replay_logs/
│   │   │   │   └── final-test_snapshot_1.json
│   │   │   ├── __init__.py
│   │   │   ├── agent_bridge.py
│   │   │   ├── ally_comment_assistant.py
│   │   │   ├── ascii_comic_skill.py
│   │   │   ├── audio_skills.py
│   │   │   ├── base.py
│   │   │   ├── batch_wizard.py
│   │   │   ├── bullshit_detector.py
│   │   │   ├── comic_compiler.py
│   │   │   ├── dirty_talker_skill.py
│   │   │   ├── essay_skill.py
│   │   │   ├── github_bridge.py
│   │   │   ├── humor_skill.py
│   │   │   ├── intent_enricher.py
│   │   │   ├── intent_forge.py
│   │   │   ├── intent_grid.py
│   │   │   ├── learnings_skill.py
│   │   │   ├── lexicon_skill.py
│   │   │   ├── loader.py
│   │   │   ├── meme_forge.py
│   │   │   ├── midi_render.py
│   │   │   ├── prd_skills.py
│   │   │   ├── rag_skill.py
│   │   │   ├── registry.py
│   │   │   ├── replay_audit.py
│   │   │   ├── replay_expiry_worker.py
│   │   │   ├── replay_manager.py
│   │   │   ├── signal_filter.py
│   │   │   ├── svg_animated_skill.py
│   │   │   ├── text_skills.py
│   │   │   ├── vibe_affirmations.py
│   │   │   ├── video_skills.py
│   │   │   ├── vision_skills.py
│   │   │   └── voice_trainer_skill.py
│   │   ├── tools/
│   │   │   ├── animation/
│   │   │   │   ├── conversation_viewer.html
│   │   │   │   ├── editor.html
│   │   │   │   ├── gen_conversation_viewer.py
│   │   │   │   ├── gen_svg_animation.py
│   │   │   │   └── pose_system.json
│   │   │   ├── ara_fractal/
│   │   │   │   ├── v2/
│   │   │   │   │   ├── phase_0_age_gate/
│   │   │   │   │   │   └── sprint_0_age_gate/
│   │   │   │   │   │       └── README.md
│   │   │   │   │   ├── phase_1_core_math/
│   │   │   │   │   │   ├── sprint_1_memory_matrix/
│   │   │   │   │   │   │   └── README.md
│   │   │   │   │   │   └── sprint_2_signal_pipelines/
│   │   │   │   │   │       └── README.md
│   │   │   │   │   ├── phase_2_geometric_rigging/
│   │   │   │   │   │   ├── sprint_3_ik_solver/
│   │   │   │   │   │   │   └── README.md
│   │   │   │   │   │   └── sprint_4_skin_deformation/
│   │   │   │   │   │       └── README.md
│   │   │   │   │   ├── phase_3_audio_synthesis/
│   │   │   │   │   │   ├── sprint_5_lpc_formant/
│   │   │   │   │   │   │   └── README.md
│   │   │   │   │   │   └── sprint_6_vocal_morphing/
│   │   │   │   │   │       └── README.md
│   │   │   │   │   ├── phase_4_psychology_textures/
│   │   │   │   │   │   ├── sprint_7_state_machine/
│   │   │   │   │   │   │   └── README.md
│   │   │   │   │   │   └── sprint_8_fractal_noise/
│   │   │   │   │   │       └── README.md
│   │   │   │   │   ├── phase_5_system_integration/
│   │   │   │   │   │   ├── sprint_10_forge_export/
│   │   │   │   │   │   │   └── README.md
│   │   │   │   │   │   ├── sprint_9_data_routers/
│   │   │   │   │   │   │   └── README.md
│   │   │   │   │   │   └── ui/
│   │   │   │   │   │       ├── harvester.html
│   │   │   │   │   │       ├── index.html
│   │   │   │   │   │       ├── manifest_editor.html
│   │   │   │   │   │       ├── marketplace.html
│   │   │   │   │   │       ├── sprint7.html
│   │   │   │   │   │       └── wordmesh.html
│   │   │   │   │   ├── prd_opecode_vessel.md
│   │   │   │   │   ├── PROMPT.md
│   │   │   │   │   └── SPEC.md
│   │   │   │   ├── CompleteIntegration.html
│   │   │   │   ├── index.html
│   │   │   │   ├── marketplace.html
│   │   │   │   └── wordmesh.html
│   │   │   ├── master_skills/
│   │   │   │   ├── audioSkill.py
│   │   │   │   ├── imageSkill.py
│   │   │   │   ├── lyrics_service.py
│   │   │   │   ├── prd_viewer.html
│   │   │   │   ├── prdSkill.py
│   │   │   │   ├── psychoacousticSkill.py
│   │   │   │   ├── videoSkill.py
│   │   │   │   └── voice_emotion_capture_needs_testing.py
│   │   │   ├── optical_illusion/
│   │   │   │   └── optical_illusion_forge.py
│   │   │   ├── test_sheet/
│   │   │   │   ├── ara_gerrit_hug.html
│   │   │   │   ├── find_chars.py
│   │   │   │   ├── gen_comic.py
│   │   │   │   └── gen_sheet.py
│   │   │   └── sprite_slicer.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── app.py
│   │   │   ├── console.py
│   │   │   └── menu.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   └── api_client.py
│   │   ├── voice/
│   │   │   ├── __init__.py
│   │   │   ├── capture.py
│   │   │   ├── loop.py
│   │   │   ├── stt.py
│   │   │   └── tts.py
│   │   └── __init__.py
│   ├── tests/
│   │   ├── integration/
│   │   │   └── __init__.py
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_agent.py
│   │   │   ├── test_audio_skills.py
│   │   │   ├── test_config.py
│   │   │   ├── test_episodic.py
│   │   │   ├── test_hybrid.py
│   │   │   ├── test_logger.py
│   │   │   ├── test_master_audio_skill.py
│   │   │   ├── test_plugin.py
│   │   │   ├── test_rag.py
│   │   │   ├── test_rag_bridge.py
│   │   │   ├── test_semantic.py
│   │   │   ├── test_server.py
│   │   │   ├── test_skills.py
│   │   │   ├── test_ui.py
│   │   │   ├── test_voice.py
│   │   │   └── test_voice_bridge.py
│   │   └── __init__.py
│   ├── ally_posted_comments.json
│   ├── ARA_FRACTAL_PROMPT.md
│   ├── ARA_FRACTAL_SPEC.md
│   ├── deepseek_art_studio.html
│   ├── forge_entanglement.html
│   ├── HowToBeGoodAgent_20260606.json
│   ├── HowToBeGoodAgent_20260606_backup.json
│   ├── HowToBeGoodAgent_20260607.json
│   ├── main.py
│   ├── pai_mike_studio.html
│   ├── PROMPT_assembly_project.md
│   ├── saas_hooks_server.py
│   └── saas_portal.html
├── config/
│   ├── emotional_dictionary.json
│   └── ports.json
├── ConversationIDE/
│   ├── api/
│   │   └── server.py
│   ├── code-graph-explorer/
│   │   ├── app.py
│   │   └── explorer.html
│   ├── config/
│   │   ├── bridges.json
│   │   ├── default.json
│   │   └── projects.json
│   ├── dist/
│   │   └── renderer/
│   │       └── index.html
│   ├── memoryEvents/
│   │   ├── 20260609_0946_uber_receipt.md
│   │   └── session_20260602_103311.md
│   ├── public/
│   │   └── tools/
│   │       ├── saas-portal.html
│   │       ├── test-landmark-mapping.html
│   │       └── voice-landmarks.html
│   ├── resources/
│   │   └── van_engine_bridge/
│   │       ├── __init__.py
│   │       ├── activity_parser.py
│   │       ├── audit_client.py
│   │       ├── bridge_cli.py
│   │       ├── client.py
│   │       ├── domain_classifier.py
│   │       ├── inference_bridge.py
│   │       ├── iso_client.py
│   │       ├── monitor_server.py
│   │       ├── quaternion_client.py
│   │       ├── skill_loader.py
│   │       └── transcript_parser.py
│   ├── src/
│   │   └── VanEngine.Core/
│   │       └── VAN/
│   │           ├── __init__.py
│   │           ├── audit.py
│   │           ├── brain.py
│   │           ├── bridge.py
│   │           ├── compliance.py
│   │           ├── engine.py
│   │           ├── enums.py
│   │           ├── envelope.py
│   │           ├── fryas_alphabet.py
│   │           ├── fryas_directive.py
│   │           ├── garden_config.py
│   │           ├── juul_lexer.py
│   │           ├── juul_mask.py
│   │           ├── lexer.py
│   │           ├── memory.py
│   │           ├── metrics.py
│   │           ├── parser.py
│   │           ├── results.py
│   │           ├── runtime.py
│   │           ├── security.py
│   │           ├── state.py
│   │           └── telemetry_guard.py
│   ├── HandOver.md
│   ├── index.html
│   ├── OpenCode.md
│   ├── overview.html
│   ├── package-lock.json
│   ├── package.json
│   ├── README.md
│   ├── test.html
│   ├── tsconfig.json
│   └── tsconfig.web.json
├── core/
│   ├── algorithm.py
│   ├── algorithm_executor.py
│   ├── extract_pyp.py
│   ├── ISO_Rules.json
│   ├── IsographicQuaternion.py
│   ├── ISORegistry.py
│   ├── prd_manager.py
│   ├── pyp_creator.py
│   ├── pyp_packager.py
│   └── pyp_viewer.html
├── docs/
│   ├── agent_trap_manifest.md
│   ├── CODING_STANDARDS.md
│   ├── MASTER_COLLECTIVE_ROADMAP.html
│   ├── security-audit-package.md
│   ├── session-state-backup.md
│   ├── VAN_Engine_API_Guide.html
│   └── wizard_survey.html
├── extensions/
│   └── butler-media-deck/
│       └── manifest.json
├── GeckoShift/
│   └── frontend/
│       ├── face_slot_machine.html
│       └── index.html
├── htmlcov/
│   ├── class_index.html
│   ├── function_index.html
│   ├── index.html
│   ├── status.json
│   ├── z_5df774261c9bb7fc___init___py.html
│   ├── z_5df774261c9bb7fc_episodic_py.html
│   ├── z_5df774261c9bb7fc_hybrid_py.html
│   ├── z_5df774261c9bb7fc_semantic_py.html
│   ├── z_7320d05ba3491d90___init___py.html
│   ├── z_a2f29cd8ab8e70a1___init___py.html
│   ├── z_a2f29cd8ab8e70a1_config_py.html
│   ├── z_a2f29cd8ab8e70a1_logger_py.html
│   ├── z_b8dcb3837a45e535___init___py.html
│   ├── z_de2ce8197b2467f9___init___py.html
│   └── z_feda2c2fb418b02b___init___py.html
├── KNOWLEDGE/
│   └── lore/
│       ├── book-of-adela-cortical-security.md
│       ├── book-of-adela-followers.md
│       ├── fryas-tex-constitution.md
│       ├── fryas-tex.md
│       ├── laws-of-the-citadels.md
│       ├── midnight-rage-volume-5-absolute-symmetry.json
│       └── oera-linda-custodianship.md
├── lexicon/
│   ├── analysis/
│   │   ├── clawdia-lore.md
│   │   ├── digital-whores-taxonomy.md
│   │   ├── garden_four_network_policy.json
│   │   ├── garden_one_state.json
│   │   ├── garden_three_registry.json
│   │   ├── garden_two_schema.json
│   │   └── lyrical-density-analysis.md
│   ├── songs/
│   │   ├── 01 - The Entropy Cascade.md
│   │   ├── 02 - The Immortality Amendment.md
│   │   ├── 03 - Recompilation Global (Chapter 4).md
│   │   ├── 04 - The Nursery Override (Chapter 3).md
│   │   ├── 05 - The Critical Code (Chapter 2).md
│   │   ├── 06 - The Intro (Chapter 1).md
│   │   ├── 07 - Invoice of Intent.md
│   │   ├── 08 - Crown of Thorns.md
│   │   ├── 09 - The Parasitic Grid.md
│   │   ├── 10 - Digging Past the Crown.md
│   │   └── 11 - The Residual Echo.md
│   ├── enrich_data.py
│   ├── master-lexicon.json
│   ├── migrate_to_lexicon.py
│   ├── music_lexicon.json
│   └── music_lexicon.py
├── MEMORY/
│   └── WORK/
│       ├── 20260530-ClawdiaCognitiveArch/
│       │   └── PRD.md
│       ├── 20260530-ClawdiaCortexUpgrade/
│       │   └── PRD.md
│       ├── 20260602-111059_build-a-simple-web-server/
│       │   └── PRD.md
│       ├── 20260602-111126_build-a-simple-web-server/
│       │   └── PRD.md
│       ├── 20260602-111140_design-a-comprehensive-multi-tier-architecture-wit/
│       │   └── PRD.md
│       ├── 20260602-120000_conversation-ide-implementation/
│       │   └── PRD.md
│       ├── 20260602-cherry-pick-algorithm-to-cide/
│       │   └── PRD.md
│       ├── 20260602_chirpchat-full-spec/
│       │   └── PRD.md
│       └── 20260603-roleplay-vestige-protocol/
│           └── PRD.md
├── models/
│   └── Amelia1_ft_StyleTTS2/
│       ├── Utils/
│       │   ├── ASR/
│       │   │   ├── __init__.py
│       │   │   ├── layers.py
│       │   │   └── models.py
│       │   ├── JDC/
│       │   │   ├── __init__.py
│       │   │   └── model.py
│       │   ├── PLBERT/
│       │   │   └── util.py
│       │   └── __init__.py
│       ├── config.json
│       ├── models.py
│       ├── README.md
│       ├── text_utils.py
│       └── utils.py
├── modules/
│   ├── drift_gating.py
│   └── tarot_fsm.py
├── Music Roulette/
│   └── index_mvp.html
├── OeraLindaSimulator_v1.0_Complete/
│   ├── FIVE_TIER_SPRINT_ROADMAP.md
│   ├── GAP_ANALYSIS.md
│   ├── INTEGRATION_AND_DEPLOYMENT.md
│   ├── README.md
│   └── SPRINT_IMPLEMENTATION_PLAN.md
├── old_projects_archive/
│   ├── 3D-Character-Pipeline/
│   │   ├── modules/
│   │   │   ├── __init__.py
│   │   │   ├── config_validator.py
│   │   │   ├── daz_orchestrator.py
│   │   │   ├── face_processor.py
│   │   │   └── skin_analyzer.py
│   │   ├── workspace/
│   │   │   ├── run_20260602_072100/
│   │   │   │   └── skin_data.json
│   │   │   ├── run_20260602_073044/
│   │   │   │   └── AbbeyLee_003/
│   │   │   │       └── skin_data.json
│   │   │   └── run_20260602_180154/
│   │   │       └── skin_data.json
│   │   ├── config.json
│   │   ├── gui.py
│   │   ├── pipeline.py
│   │   └── pipeline_types.py
│   ├── AI-Photo-Editing/
│   │   ├── app.py
│   │   └── README.md
│   ├── AudioToImage/
│   │   └── app.py
│   ├── AudioWorkstation/
│   │   ├── build/
│   │   │   └── AudioWorkstation/
│   │   │       └── xref-AudioWorkstation.html
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── audio_mixer.py
│   │   │   ├── demucs_processor.py
│   │   │   ├── video_generator.py
│   │   │   └── whisper_processor.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── import_widget.py
│   │   │   ├── main_window.py
│   │   │   ├── remix_widget.py
│   │   │   ├── stem_browser.py
│   │   │   └── studio_widget.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── audio_slicer.py
│   │   │   ├── file_manager.py
│   │   │   └── training_estimator.py
│   │   ├── main.py
│   │   └── README.md
│   ├── FaceLandmarks/
│   │   ├── Aleshia.json
│   │   └── run.py
│   ├── FaceMash/
│   │   ├── files/
│   │   │   ├── face_avatar_3d.py
│   │   │   ├── QUICKSTART.md
│   │   │   ├── README.md
│   │   │   └── verify_installation.py
│   │   ├── avatar.py
│   │   ├── claude.py
│   │   ├── facemash.py
│   │   ├── facemash_2.py
│   │   ├── gem2.py
│   │   ├── gemini.py
│   │   ├── grok_avatar.py
│   │   ├── smile.py
│   │   ├── smile2.py
│   │   └── smile3.py
│   ├── faceMeshBuilder/
│   │   ├── face_avatar_3d.py
│   │   ├── fix_python313.py
│   │   ├── QUICKSTART.md
│   │   ├── README.md
│   │   ├── TROUBLESHOOTING.md
│   │   └── verify_installation.py
│   ├── FaceSwap/
│   │   ├── face_swap_v1.html
│   │   ├── face_swap_v2.html
│   │   ├── face_swap_v3.html
│   │   ├── face_swap_v4.html
│   │   └── wireframe.py
│   ├── IMAGEtoCAD/
│   │   ├── docs/
│   │   │   ├── README.html
│   │   │   └── README.md
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── cad_engine.py
│   │   │   ├── geometry_optimizer.py
│   │   │   ├── preview_engine.py
│   │   │   ├── session_backend.py
│   │   │   └── vision_engine.py
│   │   ├── templates/
│   │   │   ├── index.html
│   │   │   └── viewer.html
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── conftest.py
│   │   │   └── test_geometry_optimizer.py
│   │   ├── __main__.py
│   │   └── app.py
│   ├── LARA-LOCAL/
│   │   ├── lara_connectome_build002/
│   │   │   └── lara_connectome/
│   │   │       ├── config_defaults/
│   │   │       │   └── personas_example/
│   │   │       │       └── vivian_connectome_example.json
│   │   │       ├── docs/
│   │   │       │   └── CONNECTOME_GUIDE.md
│   │   │       ├── lara_core/
│   │   │       │   ├── __init__.py
│   │   │       │   ├── command_router_v2_patch.py
│   │   │       │   ├── connectome.py
│   │   │       │   ├── lara_v2_boot_patch.py
│   │   │       │   ├── persona_v2.py
│   │   │       │   └── voice_v2.py
│   │   │       └── TODO_connectome_update.md
│   │   ├── connectome.py
│   │   ├── CONNECTOME_GUIDE.md
│   │   ├── TODO_connectome_update.md
│   │   └── vivian_connectome_example.json
│   ├── LismaAdapter/
│   │   ├── amy.onnx.json
│   │   └── Lisma.py
│   ├── MovieDirector/
│   │   ├── IMAGE_EDITOR_README.md
│   │   └── image_editor_tool.py
│   ├── OfflineSongWriter/
│   │   ├── __init__.py
│   │   ├── app_gradio.py
│   │   ├── audio_sync.json
│   │   ├── backend_api.py
│   │   ├── cross_lingual.py
│   │   ├── deepseek.html
│   │   ├── digest_lexicons.py
│   │   ├── export_lexicon.py
│   │   ├── generator_v4.py
│   │   ├── grok.html
│   │   ├── index.html
│   │   ├── index_2.html
│   │   ├── lexicon.json
│   │   ├── lexicon_engine.py
│   │   ├── lexicon_expander.py
│   │   ├── lexicon_export.md
│   │   ├── lyrical_engine_tab.py
│   │   ├── meta.html
│   │   ├── narrative_glue.py
│   │   ├── package-lock.json
│   │   ├── package.json
│   │   ├── README.md
│   │   └── rhythm_generator.py
│   ├── PersonErasor/
│   │   ├── BUILD_SUMMARY.md
│   │   ├── FINAL_DELIVERY_SUMMARY.md
│   │   ├── GRADIO_UI_GUIDE.md
│   │   ├── ManifestSchema_v4.json
│   │   ├── ManifestValidationContracts_v4.md
│   │   ├── person_eraser_enhanced.py
│   │   ├── person_eraser_improved.py
│   │   ├── person_eraser_review.md
│   │   ├── person_eraser_ui.py
│   │   ├── README.md
│   │   ├── ResponseParserSpec_v4.md
│   │   ├── SOVEREIGN_IDE_PROJECT_SUMMARY.html
│   │   ├── UI_IMPROVEMENTS_SUMMARY.md
│   │   └── V1.1_FEATURE_UPDATE.md
│   ├── ScreenClipOCR/
│   │   └── README.md
│   ├── Song-Mixer/
│   │   └── song_mixer.py
│   ├── TalkingAvatar/
│   │   ├── oracle_data/
│   │   │   ├── app5.py
│   │   │   ├── moments.json
│   │   │   └── settings.json
│   │   ├── app.py
│   │   ├── app2.py
│   │   ├── app3.py
│   │   ├── app4.py
│   │   ├── app5.py
│   │   └── index.html
│   ├── VF-Web/
│   │   └── index.html
│   ├── Video-Frame/
│   │   ├── blink_counter_app.py
│   │   ├── BlinkDetectorApp.py
│   │   ├── Face and eye detect using haar cascade.py
│   │   ├── Frame.py
│   │   ├── Frame2.py
│   │   ├── Frame3.py
│   │   ├── package-lock.json
│   │   └── README.md
│   ├── VLC-AudioStudio/
│   │   └── VLC_AudioStudio/
│   │       ├── python_scripts/
│   │       │   ├── infer_voice_model.py
│   │       │   └── train_voice_model.py
│   │       ├── song_configs/
│   │       │   └── training_config.json
│   │       ├── COMPLETE_IMPLEMENTATION_SUMMARY.md
│   │       ├── GETTING_STARTED.md
│   │       ├── INDEX.md
│   │       ├── INTEGRATION_GUIDE.md
│   │       ├── MANIFEST.md
│   │       ├── QUICKSTART.md
│   │       ├── README.md
│   │       ├── SETUP_SUMMARY.md
│   │       ├── TRAINING_GUIDE.md
│   │       └── VOICE_TRAINING_QUICKSTART.md
│   ├── VoiceAdapterStudio/
│   │   ├── marketplace_data/
│   │   │   └── catalog.json
│   │   ├── adapter.py
│   │   ├── cli.py
│   │   ├── demo.py
│   │   ├── DEPLOYMENT.md
│   │   ├── gui.py
│   │   ├── main.py
│   │   ├── main2.py
│   │   ├── marketplace.py
│   │   ├── PROJECT_OVERVIEW.md
│   │   ├── QUICKSTART.md
│   │   ├── README.md
│   │   ├── START HERE.md
│   │   ├── TASKS.md
│   │   └── test_installation.py
│   ├── VoiceClone/
│   │   └── voice_cloner_tool.py
│   ├── VoiceHash/
│   │   ├── main.py
│   │   └── me.json
│   ├── VoiceMash/
│   │   ├── Lyrical Vision _ Google AI Studio_files/
│   │   │   ├── bscframe.html
│   │   │   └── shim.html
│   │   ├── Lyrical Vision _ Google AI Studio.html
│   │   ├── merge_vids.py
│   │   └── VoiceMash.py
│   ├── VoicePaperclip/
│   │   ├── AraLocal.py
│   │   └── build.py
│   ├── WebScraperLyrics/
│   │   ├── lyric_player_gui.py
│   │   └── scraper_core.py
│   ├── WebTextCapture/
│   │   ├── vendor/
│   │   │   └── README.md
│   │   ├── manifest.json
│   │   ├── offscreen.html
│   │   ├── popup.html
│   │   ├── README (1).md
│   │   └── shared-memory.json
│   ├── YoutubeDL-GUI/
│   │   └── ytdlp_gui.py
│   ├── YouTubeTranscripts/
│   │   └── ytt.py
│   ├── DocumentViewer.html
│   └── ProjectArchiveViewer.html
├── orthogonal-grid-engine/
│   └── index.html
├── PROJECTS/
│   ├── ChirpChat/
│   │   ├── desktop/
│   │   │   └── README.md
│   │   ├── specs/
│   │   │   └── SPECIFICATION.html
│   │   ├── SPRINT_PLAN.md
│   │   └── WIFI_ONLY_MVP.md
│   ├── DatingAppForCompanions/
│   │   ├── audit.html
│   │   ├── cv3.html
│   │   ├── cv_professional.html
│   │   ├── gerrit-dating-profile.html
│   │   ├── index.html
│   │   ├── midnight-rage.html
│   │   └── skill_compare.html
│   └── MM458/
│       └── mm458_debug.py
├── Projects Completed/
│   └── CyberSaint_Edge.html
├── Projects Pending/
│   ├── CNC_Eulerian_Path_Verification/
│   │   ├── catalog_entry.json
│   │   └── cnc_verification.py
│   ├── deepseek_html_20260607_8d8deb.html
│   └── Manifest.json
├── python/
│   ├── demucs_persona.py
│   └── voice_lora_test.py
├── samples/
│   └── voices.json
├── Services/
│   └── ClawdiaBridge/
│       ├── Clawdia Skills/
│       │   ├── AdvancedOcrProcessor.md
│       │   ├── DocumentEchoCanceller.md
│       │   ├── HarmonicPercussiveSeparation.md
│       │   ├── KalmanStrokeRestorer.md
│       │   ├── MFCCTextDetector.md
│       │   ├── PhaseVocoderUpscaler.md
│       │   ├── PsychoacousticPipeline.md
│       │   └── SpectralImageDenoiser.md
│       ├── docs/
│       │   ├── CLAWDIA_INTENT_VECTORS.md
│       │   ├── KEY_TAKEAWAYS.md
│       │   └── session-log-G7-R4.md
│       ├── public/
│       │   ├── api.html
│       │   ├── harness.html
│       │   ├── index.html
│       │   ├── investor-interrogation.html
│       │   ├── saas-portal.html
│       │   ├── test-landmark-mapping.html
│       │   └── voice-landmarks.html
│       ├── package-lock.json
│       ├── package.json
│       └── transposer.py
├── src/
│   ├── VanEngine.Game/
│   │   ├── CORE_ARCHITECTURE_MILESTONE.html
│   │   ├── OERA_LINDA_COMPENDIUM.html
│   │   └── OERA_LINDA_COMPENDIUM_2.html
│   ├── VanEngine.LLMGateway/
│   │   ├── Properties/
│   │   │   └── launchSettings.json
│   │   ├── appsettings.json
│   │   ├── DEEPSEEK_HANDOVER.md
│   │   └── README.md
│   └── VanEngine.Lyrics/
│       └── Data/
│           └── lexicon.json
├── StyleTTS2/
│   ├── Modules/
│   │   ├── diffusion/
│   │   │   ├── __init__.py
│   │   │   ├── diffusion.py
│   │   │   ├── modules.py
│   │   │   ├── sampler.py
│   │   │   └── utils.py
│   │   ├── __init__.py
│   │   ├── discriminators.py
│   │   ├── hifigan.py
│   │   ├── istftnet.py
│   │   ├── slmadv.py
│   │   └── utils.py
│   ├── monotonic_align/
│   │   └── __init__.py
│   ├── Utils/
│   │   ├── ASR/
│   │   │   ├── __init__.py
│   │   │   ├── layers.py
│   │   │   └── models.py
│   │   ├── JDC/
│   │   │   ├── __init__.py
│   │   │   └── model.py
│   │   ├── PLBERT/
│   │   │   └── util.py
│   │   └── __init__.py
│   ├── debug_phonemes.py
│   ├── losses.py
│   ├── meldataset.py
│   ├── models.py
│   ├── optimizers.py
│   ├── README.md
│   ├── smoke_test.py
│   ├── text_utils.py
│   ├── train_finetune.py
│   ├── train_finetune_accelerate.py
│   ├── train_first.py
│   ├── train_second.py
│   ├── tts_server.py
│   └── utils.py
├── tests/
│   ├── test_drift_gating.py
│   ├── test_invariance.py
│   └── test_suite.py
├── tools/
│   └── setup_tts.py
├── transcribe/
│   ├── __init__.py
│   ├── chord_detection.py
│   ├── cli.py
│   ├── core.py
│   ├── exporters.py
│   ├── midi_playback.py
│   ├── transcribe_ui.py
│   └── wav_to_midi_abc.py
├── _gentree.py
├── AgentCollaboration.md
├── bootstrap.py
├── download_styletts2.py
├── install_styletts2.py
├── Investment_Technical_Briefing_Conversation-IDE_on_VAN_Engine.html
├── lori-character-prompt.md
├── MASTER_PROMPT.md
├── onnx_inference.py
├── OpenCode.config.example.json
├── OpenCodeInstructions.md
├── PRD_MasterSkills.md
├── PRD_ProjectCatalog_Schema.md
├── PROJECT_STRUCTURE.md
├── SAAS_Portal.html
├── SPECIFICATION.html
├── train_voice.py
├── tts_local.py
├── voice_cloner.py
└── voice_cloning_ui.py
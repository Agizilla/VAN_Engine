"""
VoiceAdapter Studio - GUI Module
Gradio web interface with Train, Apply, and Marketplace tabs.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import gradio as gr

from adapter import AdapterConfig, AdapterTrainer, AdapterInference, list_adapters
from marketplace import Marketplace, format_adapter_card


# Global instances
marketplace = Marketplace()


def train_adapter_gui(
    base_model_file,
    audio_file,
    adapter_name: str,
    epochs: int,
    mode: str,
    progress=gr.Progress()
) -> Tuple[str, str]:
    """
    Train adapter from GUI.
    
    Returns:
        Tuple of (status_message, adapter_path)
    """
    try:
        # Validate inputs
        if not audio_file:
            return "❌ Please upload an audio file.", ""
        
        if not adapter_name:
            return "❌ Please enter an adapter name.", ""
        
        # Save uploaded audio temporarily
        audio_path = audio_file.name if hasattr(audio_file, 'name') else str(audio_file)
        
        # Base model path
        if base_model_file:
            base_model = base_model_file.name if hasattr(base_model_file, 'name') else str(base_model_file)
        else:
            base_model = "models/base_model.onnx"
        
        # Create trainer
        config = AdapterConfig(mode=mode.lower(), epochs=epochs)
        trainer = AdapterTrainer(config)
        
        # Progress callback
        def progress_callback(epoch, total, loss):
            progress((epoch, total), desc=f"Training epoch {epoch}/{total} - Loss: {loss:.6f}")
        
        # Train
        adapter_path, stats = trainer.train(
            base_model_path=base_model,
            audio_path=audio_path,
            adapter_name=adapter_name,
            progress_callback=progress_callback
        )
        
        status = f"""
✅ Training Complete!

📁 Adapter: {adapter_name}
💾 Size: {Path(adapter_path).stat().st_size / (1024**2):.2f} MB
⏱️  Duration: {stats['duration']:.1f} seconds
📉 Final Loss: {stats['losses'][-1]:.6f}

Adapter saved to: {adapter_path}
        """
        
        return status.strip(), adapter_path
        
    except Exception as e:
        return f"❌ Training failed: {str(e)}", ""


def apply_adapter_gui(
    base_model_file,
    adapter_dropdown: str,
    backing_track_file,
    lyrics: str,
    progress=gr.Progress()
) -> Tuple[str, Optional[str]]:
    """
    Apply adapter to generate audio from GUI.
    
    Returns:
        Tuple of (status_message, audio_path)
    """
    try:
        # Validate inputs
        if not adapter_dropdown:
            return "❌ Please select an adapter.", None
        
        if not lyrics:
            return "❌ Please enter lyrics.", None
        
        # Get adapter path
        adapters = list_adapters()
        selected = next((a for a in adapters if a['name'] == adapter_dropdown), None)
        
        if not selected:
            return "❌ Selected adapter not found.", None
        
        adapter_path = selected['path']
        
        # Base model
        if base_model_file:
            base_model = base_model_file.name if hasattr(base_model_file, 'name') else str(base_model_file)
        else:
            base_model = "models/base_model.onnx"
        
        # Backing track
        backing_track = None
        if backing_track_file:
            backing_track = backing_track_file.name if hasattr(backing_track_file, 'name') else str(backing_track_file)
        
        # Generate output filename
        output_filename = f"{adapter_dropdown.replace(' ', '_')}_output.wav"
        
        # Apply adapter
        progress(0.3, desc="Loading adapter...")
        
        inference = AdapterInference()
        
        progress(0.6, desc="Generating audio...")
        
        output_path = inference.apply_adapter(
            base_model_path=base_model,
            adapter_path=adapter_path,
            lyrics=lyrics,
            backing_track_path=backing_track,
            output_path=output_filename
        )
        
        progress(1.0, desc="Complete!")
        
        status = f"""
✅ Audio Generated!

🎵 Adapter: {adapter_dropdown}
📝 Lyrics: {lyrics[:50]}{'...' if len(lyrics) > 50 else ''}
📁 Output: {output_path}
        """
        
        return status.strip(), output_path
        
    except Exception as e:
        return f"❌ Generation failed: {str(e)}", None


def refresh_adapter_list():
    """Refresh the list of available adapters."""
    adapters = list_adapters()
    return gr.Dropdown(choices=[a['name'] for a in adapters])


def get_marketplace_grid(category: str = "All", search_query: str = "") -> str:
    """Generate HTML for marketplace adapter grid."""
    # Get adapters
    if search_query:
        adapters = marketplace.search(search_query)
    elif category == "All":
        adapters = marketplace.get_all_adapters()
    else:
        adapters = marketplace.get_by_category(category)
    
    if not adapters:
        return "<div style='padding: 20px; text-align: center;'>No adapters found.</div>"
    
    # Generate HTML grid
    html = """
    <style>
        .adapter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            padding: 20px;
        }
        .adapter-card {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transition: transform 0.2s;
        }
        .adapter-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .adapter-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .adapter-author {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .adapter-description {
            font-size: 0.95em;
            margin-bottom: 15px;
            line-height: 1.4;
        }
        .adapter-meta {
            font-size: 0.85em;
            margin-bottom: 5px;
        }
        .adapter-price {
            font-size: 1.2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .buy-button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            width: 100%;
            transition: background 0.3s;
        }
        .buy-button:hover {
            background: #45a049;
        }
        .rating {
            color: #FFD700;
            font-size: 1.1em;
        }
    </style>
    <div class="adapter-grid">
    """
    
    for adapter in adapters:
        card_html = f"""
        <div class="adapter-card">
            <div class="adapter-title">{adapter['name']}</div>
            <div class="adapter-author">by {adapter['author']}</div>
            <div class="adapter-description">{adapter['description']}</div>
            <div class="adapter-meta">Category: {adapter['category']}</div>
            {f"<div class='adapter-meta'>Genre: {adapter['genre']}</div>" if adapter.get('genre') else ""}
            {f"<div class='adapter-meta'>Mood: {adapter['mood']}</div>" if adapter.get('mood') else ""}
            <div class="adapter-meta rating">{'⭐' * int(adapter['rating'])} ({adapter['rating']}/5.0)</div>
            <div class="adapter-meta">Downloads: {adapter['downloads']:,}</div>
            <div class="adapter-price">${adapter['price']}</div>
            <button class="buy-button" onclick="alert('Mock purchase of {adapter['name']}! No real payment processed.')">
                Buy Now
            </button>
        </div>
        """
        html += card_html
    
    html += "</div>"
    return html


def create_gui():
    """Create and configure Gradio interface."""
    
    with gr.Blocks(title="VoiceAdapter Studio", theme=gr.themes.Soft()) as app:
        gr.Markdown(
            """
            # 🎵 VoiceAdapter Studio
            ### Create, Apply, and Share Voice Adapters
            
            **Local Processing** • **Cross-Platform** • **No Cloud Required**
            """
        )
        
        with gr.Tabs():
            # ==================== TRAIN TAB ====================
            with gr.Tab("🎓 Train Adapter"):
                gr.Markdown("### Train a New Voice Adapter")
                
                with gr.Row():
                    with gr.Column():
                        train_base_model = gr.File(
                            label="Base Model (ONNX)",
                            file_types=[".onnx"],
                            type="filepath"
                        )
                        train_audio = gr.Audio(
                            label="Training Audio",
                            type="filepath",
                            sources=["upload"]
                        )
                        train_name = gr.Textbox(
                            label="Adapter Name",
                            placeholder="e.g., MyStyle, JazzVocal, etc."
                        )
                        
                        with gr.Row():
                            train_epochs = gr.Slider(
                                minimum=10,
                                maximum=500,
                                value=100,
                                step=10,
                                label="Training Epochs"
                            )
                            train_mode = gr.Radio(
                                choices=["Ordinary", "Pro"],
                                value="Ordinary",
                                label="Training Mode"
                            )
                        
                        train_btn = gr.Button("🚀 Start Training", variant="primary", size="lg")
                    
                    with gr.Column():
                        train_output = gr.Textbox(
                            label="Training Status",
                            lines=12,
                            interactive=False
                        )
                        train_file_output = gr.File(label="Download Trained Adapter")
                
                train_btn.click(
                    fn=train_adapter_gui,
                    inputs=[train_base_model, train_audio, train_name, train_epochs, train_mode],
                    outputs=[train_output, train_file_output]
                )
                
                gr.Markdown(
                    """
                    **Tips:**
                    - Use high-quality audio samples (WAV format recommended)
                    - Ordinary mode: CPU-only, faster, 1-3 MB adapters
                    - Pro mode: GPU-accelerated, more control, up to 5 MB adapters
                    - More epochs = better quality but longer training time
                    """
                )
            
            # ==================== APPLY TAB ====================
            with gr.Tab("🎤 Apply Adapter"):
                gr.Markdown("### Generate Audio with Adapter")
                
                with gr.Row():
                    with gr.Column():
                        apply_base_model = gr.File(
                            label="Base Model (ONNX)",
                            file_types=[".onnx"],
                            type="filepath"
                        )
                        
                        # Adapter dropdown with refresh button
                        with gr.Row():
                            apply_adapter = gr.Dropdown(
                                label="Select Adapter",
                                choices=[a['name'] for a in list_adapters()],
                                interactive=True
                            )
                            refresh_btn = gr.Button("🔄", size="sm")
                        
                        apply_backing = gr.Audio(
                            label="Backing Track (Optional)",
                            type="filepath",
                            sources=["upload"]
                        )
                        apply_lyrics = gr.Textbox(
                            label="Lyrics",
                            placeholder="Enter your lyrics here...",
                            lines=5
                        )
                        
                        apply_btn = gr.Button("🎵 Generate Audio", variant="primary", size="lg")
                    
                    with gr.Column():
                        apply_output = gr.Textbox(
                            label="Generation Status",
                            lines=8,
                            interactive=False
                        )
                        apply_audio_output = gr.Audio(
                            label="Generated Audio",
                            type="filepath"
                        )
                
                # Refresh adapter list
                refresh_btn.click(
                    fn=refresh_adapter_list,
                    outputs=[apply_adapter]
                )
                
                apply_btn.click(
                    fn=apply_adapter_gui,
                    inputs=[apply_base_model, apply_adapter, apply_backing, apply_lyrics],
                    outputs=[apply_output, apply_audio_output]
                )
                
                gr.Markdown(
                    """
                    **Tips:**
                    - Select an adapter you've trained or downloaded
                    - Add a backing track to mix with generated vocals
                    - Lyrics can be song lyrics, speech, or any text
                    - Download the generated audio and edit in your DAW
                    """
                )
            
            # ==================== MARKETPLACE TAB ====================
            with gr.Tab("🛒 Marketplace"):
                gr.Markdown("### Browse and Discover Voice Adapters")
                
                gr.Markdown(
                    """
                    **Note:** This is a mock marketplace for demonstration. 
                    "Buy" buttons simulate purchases - no real payments are processed.
                    """
                )
                
                with gr.Row():
                    market_category = gr.Dropdown(
                        label="Filter by Category",
                        choices=["All", "Genre", "Mood", "Artist Style"],
                        value="All"
                    )
                    market_search = gr.Textbox(
                        label="Search Adapters",
                        placeholder="Search by name, author, or description..."
                    )
                    market_refresh = gr.Button("🔍 Search", variant="primary")
                
                market_grid = gr.HTML(
                    value=get_marketplace_grid(),
                    label="Adapter Gallery"
                )
                
                # Update grid on filter/search
                market_refresh.click(
                    fn=get_marketplace_grid,
                    inputs=[market_category, market_search],
                    outputs=[market_grid]
                )
                
                market_category.change(
                    fn=get_marketplace_grid,
                    inputs=[market_category, market_search],
                    outputs=[market_grid]
                )
                
                gr.Markdown(
                    """
                    ### Categories Available:
                    - **Genre**: Pop, Rock, Jazz, Hip-Hop, Classical, Electronic
                    - **Mood**: Energetic, Melancholic, Romantic, Aggressive, Chill
                    - **Artist Style**: Educational vocal styles (practice only)
                    
                    ### Coming Soon:
                    - Real payment integration
                    - User uploads and reviews
                    - Audio preview samples
                    - License management
                    """
                )
        
        # Footer
        gr.Markdown(
            """
            ---
            **VoiceAdapter Studio v1.0** | MIT License | [Documentation](README.md) | [GitHub](#)
            
            Made with ❤️ using Gradio • All processing happens locally on your device
            """
        )
    
    return app


def launch(share=False, server_name="127.0.0.1", server_port=7860):
    """Launch the Gradio GUI."""
    app = create_gui()
    app.launch(
        share=share,
        server_name=server_name,
        server_port=server_port,
        show_error=True
    )


if __name__ == "__main__":
    launch()

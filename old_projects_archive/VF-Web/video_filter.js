// --- Global Helper Function ---
// This function must be defined globally so the application logic can use it to log status.
window.showMessage = function(text, type = 'info') {
    const messageBox = $('#messageBox');
    // Ensure jQuery element exists before trying to manipulate it
    if (messageBox.length === 0) {
        console.warn("Message box element not found in DOM.");
        return;
    }

    messageBox.removeClass('d-none');
    messageBox.find('.alert')
        .removeClass('alert-danger alert-warning alert-info alert-success')
        .addClass('alert-' + type)
        .text(text);
};

// Maps a persistence count (0 to THRESHOLD) to an RGB color array [R, G, B] for visualization.
// It creates a heatmap: Blue (low count) -> Red (high count).
function mapPersistenceToColor(count, threshold) {
    // Normalize count to a value between 0 (low persistence) and 1 (high persistence)
    const normalized = Math.min(1, count / threshold);

    // Value from 0 to 255
    const value = Math.round(normalized * 255);

    // Red component increases as value goes from 0 to 255 (i.e., Blue fades out, Red fades in)
    const r = value;
    // Blue component decreases as value goes from 0 to 255
    const b = 255 - value;
    // Green is always zero in this simple heatmap
    const g = 0;

    return [r, g, b];
}

// --- Main Application Logic (Runs when the DOM is fully loaded) ---
$(document).ready(function() {
    // --- DOM Elements ---
    const $videoFile = $('#videoFile');
    const $videoSource = $('#video-source');
    const $canvas = $('#video-canvas');
    const canvas = $canvas[0];
    // Ensure we have a canvas context
    const ctx = canvas.getContext('2d', { willReadFrequently: true });

    const $toggleFilterBtn = $('#toggleFilterBtn');
    const $playPauseBtn = $('#playPauseBtn');
    const $playPauseIcon = $('#playPauseIcon');
    const $playPauseText = $('#playPauseText');
    const $stepForwardBtn = $('#stepForwardBtn');
    const $stepBackBtn = $('#stepBackBtn');
    const $screenshotBtn = $('#screenshotBtn');
    const $filterStatus = $('#filterStatus');
    const $thresholdInput = $('#thresholdInput');
    const $toleranceInput = $('#toleranceInput');
    const $toleranceValue = $('#toleranceValue');
    const $toggleVisualization = $('#toggleVisualization');

    // --- State Variables ---
    let isFilterActive = false;
    let isVisualizationActive = false;
    let previousFrameData = null; // Stores the ImageData.data array of the previous frame
    let persistenceMap = null;    // Stores the per-pixel persistence count (Uint8Array)
    let animationFrameId = null;

    let videoWidth = 0;
    let videoHeight = 0;
    const FRAME_STEP = 1 / 30; // Approximately 30 frames per second (0.0333 seconds)

    // --- Configuration ---
    let THRESHOLD = parseInt($thresholdInput.val()); // Max count before turning black
    let TOLERANCE = parseInt($toleranceInput.val()); // Max color difference (sum of R, G, B diffs) to count as 'no change'

    // Function to calculate the difference between two pixel colors
    function colorDifference(idx, data1, data2) {
        // idx is the index of the Red channel (i * 4)
        let diff = Math.abs(data1[idx] - data2[idx]) +      // R difference
                   Math.abs(data1[idx + 1] - data2[idx + 1]) + // G difference
                   Math.abs(data1[idx + 2] - data2[idx + 2]);  // B difference
        return diff;
    }

    // Function to enable/disable all control buttons
    function setControlsEnabled(enabled) {
        $toggleFilterBtn.prop('disabled', !enabled);
        $playPauseBtn.prop('disabled', !enabled);
        $stepForwardBtn.prop('disabled', !enabled);
        $stepBackBtn.prop('disabled', !enabled);
        $screenshotBtn.prop('disabled', !enabled);
        $toggleVisualization.prop('disabled', !enabled); // Also enable/disable the toggle
    }

    // --- Core Frame Processing Logic ---
    function captureFrameAndApplyFilter() {
        if (videoWidth === 0) return;

        // 1. Draw the current video frame onto the canvas
        ctx.drawImage($videoSource[0], 0, 0, videoWidth, videoHeight);

        // 2. Get the current pixel data
        let currentFrame = ctx.getImageData(0, 0, videoWidth, videoHeight);
        let currentData = currentFrame.data;

        if (isFilterActive && previousFrameData) {
            // --- APPLY PERSISTENCE FILTER ---
            const totalPixels = videoWidth * videoHeight;

            for (let i = 0; i < totalPixels; i++) {
                const dataIndex = i * 4; // Index for R channel

                // Calculate color difference between current and previous frame at this pixel
                const diff = colorDifference(dataIndex, currentData, previousFrameData);

                if (diff > TOLERANCE) {
                    // PIXEL CHANGED significantly
                    persistenceMap[i] = 0; // Reset persistence count
                } else {
                    // PIXEL DID NOT CHANGE (it is static)
                    if (persistenceMap[i] < THRESHOLD) {
                        // Not persistent enough yet, just increment
                        persistenceMap[i]++;
                    }

                    // --- APPLY VISUALIZATION OR FINAL FILTER ---
                    if (isVisualizationActive) {
                        // Visualization Mode: Color shows persistence count (Blue to Red heatmap)
                        const count = persistenceMap[i];
                        const [r, g, b] = mapPersistenceToColor(count, THRESHOLD);

                        currentData[dataIndex] = r;     // R
                        currentData[dataIndex + 1] = g; // G
                        currentData[dataIndex + 2] = b; // B
                        // Alpha remains 255
                    } else if (persistenceMap[i] >= THRESHOLD) {
                        // Standard Filter Mode: Pixel is persistent, set to black
                        currentData[dataIndex] = 0;     // R
                        currentData[dataIndex + 1] = 0; // G
                        currentData[dataIndex + 2] = 0; // B
                        currentData[dataIndex + 3] = 255; // A (Fully opaque)
                    }
                }
            }

            // 3. Put the modified data back onto the canvas
            ctx.putImageData(currentFrame, 0, 0);

        }

        // 4. Save the current frame data for the next comparison, regardless of filter state
        // Only save if the filter is active, otherwise keep it null
        if (isFilterActive) {
            // Save a copy of the current data for the next frame's comparison
            previousFrameData = new Uint8ClampedArray(currentData);
        }
    }


    // --- Main Video Processing Loop ---
    function processVideoFrame() {
        if ($videoSource[0].paused || $videoSource[0].ended) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
            return;
        }

        captureFrameAndApplyFilter();

        // Request the next frame
        animationFrameId = requestAnimationFrame(processVideoFrame);
    }

    // --- Control Handlers ---

    // Play/Pause Toggle
    $playPauseBtn.on('click', function() {
        const video = $videoSource[0];
        if (video.paused || video.ended) {
            video.play();
        } else {
            video.pause();
        }
    });

    // Update UI when video state changes (play/pause)
    $videoSource.on('play', function() {
        $playPauseIcon.removeClass('fa-play').addClass('fa-pause');
        $playPauseText.text('Pause');
        window.showMessage('Video playing. Filter is ' + (isFilterActive ? 'ON.' : 'OFF.'));
        if (!animationFrameId) {
            animationFrameId = requestAnimationFrame(processVideoFrame);
        }
    }).on('pause', function() {
        $playPauseIcon.removeClass('fa-pause').addClass('fa-play');
        $playPauseText.text('Play');
        window.showMessage('Video paused. Use "Prev/Next" to step frame-by-frame.', 'warning');
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
    });

    // Step Forward
    $stepForwardBtn.on('click', function() {
        const video = $videoSource[0];
        if (!video.paused) {
            video.pause(); // Pause if playing for accurate step
        }
        // Advance time by one frame duration (clamped by video duration)
        video.currentTime = Math.min(video.duration, video.currentTime + FRAME_STEP);
        // Manually process the frame after seeking
        captureFrameAndApplyFilter();
        window.showMessage(`Stepped forward to ${video.currentTime.toFixed(3)}s.`, 'info');
    });

    // Step Backward (Note: frame accuracy is limited by browser seeking)
    $stepBackBtn.on('click', function() {
        const video = $videoSource[0];
        if (!video.paused) {
            video.pause(); // Pause if playing for accurate step
        }
        // Move time back by one frame duration (clamped at 0)
        video.currentTime = Math.max(0, video.currentTime - FRAME_STEP);
        // Manually process the frame after seeking
        captureFrameAndApplyFilter();
        window.showMessage(`Stepped backward to ${video.currentTime.toFixed(3)}s.`, 'info');
    });

    // Screenshot Button
    $screenshotBtn.on('click', function() {
        if (videoWidth === 0) {
            window.showMessage('Please load a video first to take a screenshot.', 'warning');
            return;
        }
        // Use the canvas's current state to create an image URL
        const dataURL = canvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = dataURL;
        a.download = 'video-persistence-screenshot-' + new Date().toISOString().slice(0, 19).replace('T', '-').replace(/:/g, '') + '.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.showMessage('Screenshot saved!', 'success');
    });


    // 1. Load Video File
    $videoFile.on('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const videoUrl = URL.createObjectURL(file);
            $videoSource.attr('src', videoUrl);
            window.showMessage('Video file loaded. Waiting for metadata...');

            setControlsEnabled(false); // Disable controls until ready

            // When video metadata is loaded, set canvas dimensions and start playing
            $videoSource.one('loadedmetadata', function() {
                videoWidth = this.videoWidth;
                videoHeight = this.videoHeight;

                // Set canvas to match video dimensions
                canvas.width = videoWidth;
                canvas.height = videoHeight;

                // Initialize persistence map (W * H size, using Uint8 for 0-255 count)
                const totalPixels = videoWidth * videoHeight;
                persistenceMap = new Uint8Array(totalPixels).fill(0);

                setControlsEnabled(true); // Enable controls
                window.showMessage('Video ready. Press Play to start processing.');

                // Pause initially to allow user to configure filter
                this.pause();
                captureFrameAndApplyFilter(); // Draw first frame
            });
        }
    });

    // 2. Toggle Main Filter Button
    $toggleFilterBtn.on('click', function() {
        if (videoWidth === 0) {
            window.showMessage('Please load a video first.', 'warning');
            return;
        }

        isFilterActive = !isFilterActive;

        if (isFilterActive) {
            // Filter just turned ON
            const filterStateText = isVisualizationActive ? 'Filter ON (Debug Mode)' : 'Filter ON';
            $filterStatus.text(filterStateText);
            $toggleFilterBtn.removeClass('btn-danger').addClass('btn-success');

            // Re-initialize map and previous data when turning ON
            const totalPixels = videoWidth * videoHeight;
            persistenceMap = new Uint8Array(totalPixels).fill(0);
            previousFrameData = null; // Will be set after the first processed frame
            window.showMessage('Persistence filter activated. Background will start to disappear.', 'danger');

        } else {
            // Filter just turned OFF
            $filterStatus.text('Filter OFF');
            $toggleFilterBtn.removeClass('btn-success').addClass('btn-danger');

            // If visualization was active, turn it off too
            isVisualizationActive = false;
            $toggleVisualization.prop('checked', false);

            previousFrameData = null;
            persistenceMap = null;
            window.showMessage('Persistence filter deactivated. Showing raw video.', 'success');

            // When filter is off, redraw the current video frame without processing
            captureFrameAndApplyFilter();
        }
    });

    // 3. Toggle Visualization Button (NEW)
    $toggleVisualization.on('change', function() {
        isVisualizationActive = $(this).is(':checked');

        if (isVisualizationActive) {
            // If visualization is turned on, force the main filter ON for the map to be calculated
            if (!isFilterActive) {
                isFilterActive = true;
                $toggleFilterBtn.removeClass('btn-danger').addClass('btn-success');
                // Re-initialize map as we just turned the filter on
                const totalPixels = videoWidth * videoHeight;
                persistenceMap = new Uint8Array(totalPixels).fill(0);
                previousFrameData = null;
            }
            $filterStatus.text('Filter ON (Debug Mode)');
            window.showMessage('Visualization enabled. Filter is ON and showing a Blue-to-Red heatmap.', 'info');
        } else if (!isVisualizationActive && isFilterActive) {
            // If visualization is turned off but filter is still on, restore standard filter status text
            $filterStatus.text('Filter ON');
            window.showMessage('Visualization disabled. Standard filter effect (black background) is active.', 'info');
        }

        // Manually process frame if video is paused to update display immediately
        if ($videoSource[0].paused) {
            captureFrameAndApplyFilter();
        }
    });

    // 4. Configuration Updates
    $thresholdInput.on('input', function() {
        THRESHOLD = parseInt($(this).val());
        // Manually process frame if video is paused to update display immediately
        if ($videoSource[0].paused) {
            captureFrameAndApplyFilter();
        }
    });

    $toleranceInput.on('input', function() {
        TOLERANCE = parseInt($(this).val());
        $toleranceValue.text(TOLERANCE);
    });

    // Initial state message
    window.showMessage('Welcome! Load a video file to begin.');

    // Prevent default right-click context menu on canvas (common for video apps)
    $canvas.on('contextmenu', function(e){
        e.preventDefault();
    });
});

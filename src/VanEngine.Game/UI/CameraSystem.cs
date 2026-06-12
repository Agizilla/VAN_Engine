using System.Numerics;
using Raylib_CsLo;
using static Raylib_CsLo.Raylib;

namespace VanEngine.Game.UI;

public sealed class CameraSystem
{
    private Camera2D _camera;
    private bool _isPanning;
    private Vector2 _panStartMouse;
    private Vector2 _panStartTarget;
    public float MinZoom { get; set; } = 0.5f;
    public float MaxZoom { get; set; } = 3.0f;

    public Camera2D Camera => _camera;

    public CameraSystem()
    {
        _camera = new Camera2D
        {
            target = new Vector2(0, 0),
            offset = new Vector2(0, 0),
            rotation = 0f,
            zoom = 1.0f,
        };
    }

    public void Update()
    {
        float wheel = GetMouseWheelMove();
        if (wheel != 0)
        {
            float prevZoom = _camera.zoom;
            _camera.zoom = Math.Clamp(_camera.zoom + wheel * 0.1f, MinZoom, MaxZoom);

            Vector2 mouse = GetMousePosition();
            _camera.target.X += (mouse.X - _camera.offset.X) * (1f / prevZoom - 1f / _camera.zoom) / (1f / _camera.zoom);
            _camera.target.Y += (mouse.Y - _camera.offset.Y) * (1f / prevZoom - 1f / _camera.zoom) / (1f / _camera.zoom);
        }

        if (IsMouseButtonPressed(MouseButton.MOUSE_BUTTON_MIDDLE))
        {
            _isPanning = true;
            _panStartMouse = GetMousePosition();
            _panStartTarget = _camera.target;
        }

        if (_isPanning)
        {
            Vector2 mouse = GetMousePosition();
            _camera.target.X = _panStartTarget.X - (mouse.X - _panStartMouse.X) / _camera.zoom;
            _camera.target.Y = _panStartTarget.Y - (mouse.Y - _panStartMouse.Y) / _camera.zoom;

            if (IsMouseButtonReleased(MouseButton.MOUSE_BUTTON_MIDDLE))
                _isPanning = false;
        }

        int edgeScroll = 20;
        float scrollSpeed = 8f / _camera.zoom;
        Vector2 m = GetMousePosition();
        if (m.X < edgeScroll) _camera.target.X -= scrollSpeed;
        if (m.X > GetScreenWidth() - edgeScroll) _camera.target.X += scrollSpeed;
        if (m.Y < edgeScroll) _camera.target.Y -= scrollSpeed;
        if (m.Y > GetScreenHeight() - edgeScroll) _camera.target.Y += scrollSpeed;
    }

    public void BeginView() => BeginMode2D(_camera);
    public void EndView() => EndMode2D();

    public Vector2 ScreenToWorld(Vector2 screenPos)
    {
        return GetScreenToWorld2D(screenPos, _camera);
    }

    public void ResetView()
    {
        _camera.target = new Vector2(0, 0);
        _camera.zoom = 1.0f;
    }

    public void FocusOn(float x, float y)
    {
        _camera.target = new Vector2(x - GetScreenWidth() / 2f, y - GetScreenHeight() / 2f);
    }
}

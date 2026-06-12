def main():
    from clawdia.src.ui.app import ClawDiaApp
    import sys
    skills_dir = None
    if len(sys.argv) > 1:
        skills_dir = sys.argv[1]
    app = ClawDiaApp(skills_dir)
    app.run()


if __name__ == "__main__":
    main()

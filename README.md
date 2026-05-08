Background Pingu has originally been a Discord bot designed for automatic parsing of Minecraft logs, primarily for the MCSR (Minecraft Speedrunning) community. Now it's also available as a website.

## Features

- Supports paste.ee and mclo.gs links, as well as Discord attached files.
- Uploads logs to mclo.gs.
- Automatically detects lots of common issues.

## Issue detection

Issue detection was mostly made with MultiMC / Prism Launcher `Minecraft log`'s log format in mind. It will still try to find issues in latest.log's / crash-reports, but support for them is limited.

A lot of common Minecraft issues should be detected, including mod crashes, as well as some MultiMC/Prism issues.

## Development

### Running the project

All commands are supposed to be ran from the repository root.

If you don't have it installed, install `uv`: https://docs.astral.sh/uv/getting-started/installation/

Before launching, optional:
`uv sync --all-packages`

Running the Discord bot:
`uv run --package discord python -m BackgroundPingu.run`

Running the log checker website:
`uv run --directory web uvicorn app:app --host 0.0.0.0 --port 8001`

Running the SeedQueue settings website:
`uv run --directory web-sq uvicorn app:app --host 0.0.0.0 --port 8000`

### Contributing

Contributions are welcome! If you have any suggestions, bug reports, or feature requests, feel free to reach out to `maskers` on Discord.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.

## Contact

For any suggestions or questions, please reach out to `maskers` on Discord.

## Legal Links

- [Privacy Policy](./PRIVACY_POLICY.md)
- [Terms of Service](./TERMS_OF_SERVICE.md)
- [License](./LICENSE)
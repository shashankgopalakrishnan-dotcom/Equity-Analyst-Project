"""Read the Week 1 .env values without printing the full API key."""

from pathlib import Path


def read_env_file(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE lines, including quoted values with spaces."""
    if not path.is_file():
        raise FileNotFoundError(f"Could not find {path}. Run this script from the course folder.")

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}: expected KEY=VALUE.")

        name, value = line.split("=", maxsplit=1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[name] = value
    return values


def main() -> None:
    values = read_env_file(Path(__file__).with_name(".env"))
    api_key = values.get("API_KEY", "")
    sec_user_agent = values.get("SEC_USER_AGENT", "")

    if not api_key:
        raise ValueError("API_KEY is empty. Add your key to .env, then run this script again.")
    if not sec_user_agent:
        raise ValueError("SEC_USER_AGENT is empty. Add your name and Purdue email to .env.")

    print(f"API_KEY: {api_key[:4]}...")
    print(f"SEC_USER_AGENT: {sec_user_agent}")
    if api_key == "paste-here":
        print("Note: .env is readable, but API_KEY is still the placeholder. Replace it locally to finish the lab check.")
    if "[your name]" in sec_user_agent or "[your Purdue email]" in sec_user_agent:
        print("Note: replace the SEC_USER_AGENT placeholders with your name and Purdue email.")


if __name__ == "__main__":
    main()

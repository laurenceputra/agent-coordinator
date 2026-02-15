from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / ".agents" / "skills"
EXPECTED_SKILLS = {
    "execution-runtime",
    "decision-policy",
    "docker-auth-runtime",
    "verification-gates",
}


def test_skills_have_expected_directories_and_frontmatter() -> None:
    skill_dirs = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    assert skill_dirs == EXPECTED_SKILLS, f"Skill directories mismatch: {skill_dirs}"

    for skill_name in sorted(skill_dirs):
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        assert skill_file.exists(), f"Missing {skill_file}"
        content = skill_file.read_text(encoding="utf-8")
        assert content.startswith("---\n"), f"Missing YAML frontmatter in {skill_file}"
        assert "\nname:" in content
        assert "\ndescription:" in content


def test_agents_lists_exactly_expected_skills() -> None:
    agents_md = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    listed = set(re.findall(r"\.agents/skills/([a-z0-9-]+)", agents_md))
    assert listed == EXPECTED_SKILLS, f"AGENTS.md skill list mismatch: {listed}"

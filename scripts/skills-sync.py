#!/usr/bin/env python3
"""
🎯 Skills Sync Pipeline v1
=========================
Auto-discovers new relevant skills from aradotso/trending-skills (496+ skills)
and imports them into Hermes.

Run: python3 ~/.hermes/scripts/skills-sync.py
Cron: 0 5 * * * (daily at 5am)
"""
import json, urllib.request, urllib.error, base64, os, sys, re, time, subprocess
from datetime import datetime

# === Config ===
SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
LOG_DIR = os.path.expanduser("~/.hermes/logs")
STATE_FILE = os.path.expanduser("~/.hermes/data/skills-sync-state.json")
os.makedirs(SKILLS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

REPOS = {
    "trending": {
        "url": "aradotso/trending-skills",
        "path": "skills",
        "prefix": "trending",
        "stars": "trending",
        "desc": "Auto-generated from GitHub trending"
    },
    "addyosmani": {
        "url": "addyosmani/agent-skills",
        "path": "skills",
        "prefix": "addyosmani",
        "stars": "44K",
        "desc": "Production-grade engineering skills"
    },
    "vercel": {
        "url": "vercel-labs/agent-skills",
        "path": "skills",
        "prefix": "vercel",
        "stars": "26.8K",
        "desc": "Vercel official agent skills"
    },
    "science": {
        "url": "K-Dense-AI/scientific-agent-skills",
        "path": "scientific-skills",
        "prefix": "science",
        "stars": "24.8K",
        "desc": "Scientific/research/engineering skills"
    },
}

# Categories we auto-import (new skills matching these = auto-add)
AUTO_IMPORT_CATEGORIES = [
    # WeChat / social content platforms
    "wechat", "weixin", "wx-", "dingtalk", "wecom",
    "微信公众号", "公众号",
    # Content creation
    "write", "content", "publish", "blog", "article", "seo",
    "markdown", "newsletter", " editorial",
    # Image & video
    "image", "video", "gpt-image", "photo", "illustrat",
    "animat", "screenshot", "poster",
    # Design
    "design", "ui-ux", "css", "html", "ppt", "slide",
    "poster", "typography", "font", "color",
    # Agent infrastructure
    "agent-", "-agent", "harness", "orchestrat",
    "skill", "loop", "autoresearch",
    # Coding tools
    "codex", "claude-code", "gemini", "cursor",
    "aider", "opencode",
    # Data
    "data", "analytics", "chart", "visualiz",
    "dashboard",
    # Knowledge
    "memory", "knowledge", "wiki", "obsidian",
    "note", "brain",
    # Research
    "research", "paper", "citation", "literature",
    "arxiv", "academic",
    # Productivity
    "pdf", "docx", "xlsx", "workflow", "automation",
    "cli", "terminal",
]

# === Auth ===
def get_token():
    try:
        result = subprocess.run(
            ['git', 'credential-store', 'get'],
            input='protocol=https\nhost=github.com\n',
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().split('\n'):
            if line.startswith('password='):
                return line[9:]
    except: pass
    try:
        with open(os.path.expanduser('~/.git-credentials')) as f:
            for line in f:
                if 'github.com' in line and '://' in line:
                    return line.split('://')[1].split('@')[0].split(':')[-1]
    except: pass
    return None

GH_TOKEN = get_token()
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GH_TOKEN:
    HEADERS["Authorization"] = f"token {GH_TOKEN}"

# === GitHub API ===
def gh_api(url):
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if e.code == 403 and "rate" in body.lower():
                time.sleep(30); continue
            return None
    return None

def gh_raw(url):
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    except:
        return None

def b64decode(data):
    if "content" not in data: return None
    return base64.b64decode(data["content"]).decode("utf-8")

# === Skill Operations ===
def normalize_name(name):
    name = name.lower().replace("_", "-").replace(" ", "-")
    name = re.sub(r'[^a-z0-9-]', '', name)
    name = re.sub(r'-+', '-', name).strip('-')
    return name

def skill_exists(name):
    return os.path.isdir(os.path.join(SKILLS_DIR, name))

def skill_file_exists(name):
    return os.path.isfile(os.path.join(SKILLS_DIR, name, "SKILL.md"))

def get_installed_skills():
    """Return set of installed skill names"""
    skills = set()
    for d in os.listdir(SKILLS_DIR):
        if os.path.isdir(os.path.join(SKILLS_DIR, d)):
            if os.path.isfile(os.path.join(SKILLS_DIR, d, "SKILL.md")):
                skills.add(d)
    return skills

def is_relevant(name):
    """Check if skill name matches our auto-import categories"""
    nl = name.lower()
    for cat in AUTO_IMPORT_CATEGORIES:
        if cat in nl:
            return True
    return False

def add_attribution(md, repo_url, stars, desc):
    attr = f"\n---\n*Imported from [{repo_url}](https://github.com/{repo_url}) — ⭐{stars} — {desc}*\n"
    if md.strip().startswith("---"):
        parts = md.split("---", 2)
        if len(parts) >= 3:
            return parts[0] + "---" + parts[1] + "---" + attr + "\n" + parts[2]
    return md + attr

def import_skill(name, content):
    d = os.path.join(SKILLS_DIR, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(content)

# === Sync Engine ===
def sync_repo(repo_key, repo_info):
    """Sync a single repo: discover new skills, import if relevant"""
    repo = repo_info["url"]
    path = repo_info["path"]
    prefix = repo_info["prefix"]
    stars = repo_info["stars"]
    desc = repo_info["desc"]
    
    installed = get_installed_skills()
    
    # Fetch all skill dirs
    all_items = gh_api(f"https://api.github.com/repos/{repo}/contents/{path}")
    if not all_items:
        return {"repo": repo_key, "new": 0, "skipped": 0, "error": "Cannot access repo"}
    
    skill_names = [s["name"] for s in all_items if s["type"] == "dir"]
    
    new_count = 0
    skipped_count = 0
    new_skills = []
    
    for name in skill_names:
        final_name = f"{prefix}-{normalize_name(name)}"
        
        if final_name in installed:
            skipped_count += 1
            continue
        
        # Check relevance
        if not is_relevant(name):
            skipped_count += 1
            continue
        
        # Fetch SKILL.md
        md = None
        data = gh_api(f"https://api.github.com/repos/{repo}/contents/{path}/{name}/SKILL.md")
        if data and "content" in data:
            md = b64decode(data)
        
        if not md:
            items = gh_api(f"https://api.github.com/repos/{repo}/contents/{path}/{name}")
            if items and isinstance(items, list):
                for item in items:
                    if item["name"] == "SKILL.md" and "content" in item:
                        md = b64decode(item)
                        break
        
        if not md:
            skipped_count += 1
            continue
        
        md = add_attribution(md, repo, stars, desc)
        import_skill(final_name, md)
        new_count += 1
        new_skills.append(final_name)
        
        # Rate limit protection
        if new_count % 10 == 0:
            time.sleep(1)
    
    return {
        "repo": repo_key,
        "total_available": len(skill_names),
        "new": new_count,
        "skipped": skipped_count,
        "new_skills": new_skills
    }

# === Main ===
def main():
    start = datetime.now()
    print(f"🔧 Skills Sync Pipeline — {start.strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    
    # Load previous state
    prev_state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                prev_state = json.load(f)
        except: pass
    
    results = []
    total_new = 0
    all_new_skills = []
    
    for key, info in REPOS.items():
        print(f"\n📦 {key} ({info['desc']})...")
        result = sync_repo(key, info)
        results.append(result)
        total_new += result["new"]
        all_new_skills.extend(result["new_skills"])
        
        if result.get("error"):
            print(f"  ⚠️  {result['error']}")
        else:
            print(f"  {result['new']} new, {result['skipped']} existing/skipped (of {result['total_available']} total)")
    
    # Save state
    state = {
        "last_run": start.isoformat(),
        "total_skills": len(get_installed_skills()),
        "total_new": total_new,
        "new_skills": all_new_skills,
        "results": results
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    # Summary
    elapsed = (datetime.now() - start).total_seconds()
    total = len(get_installed_skills())
    
    print(f"\n{'='*60}")
    print(f"📊 Summary")
    print(f"   New skills imported: {total_new}")
    if all_new_skills:
        print(f"   Skills added: {', '.join(all_new_skills[:20])}")
        if len(all_new_skills) > 20:
            print(f"   ... and {len(all_new_skills) - 20} more")
    print(f"   Total Hermes skills: {total}")
    print(f"   Duration: {elapsed:.1f}s")
    print(f"   State saved: {STATE_FILE}")
    
    # Return results as JSON for cron delivery
    return state

if __name__ == "__main__":
    result = main()
    # Print final JSON for cron context delivery
    print(f"\n---STATE_JSON---")
    print(json.dumps({
        "total_skills": result["total_skills"],
        "total_new": result["total_new"],
        "new_skills": result["new_skills"][:30],
        "timestamp": result["last_run"]
    }, ensure_ascii=False))

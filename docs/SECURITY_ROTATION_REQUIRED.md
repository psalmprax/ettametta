# SECURITY: Key Rotation Required

## RSA Private Key (`key_raw.txt`)

An RSA private key was committed to this repository's git history and has been removed via `git filter-repo`. However:

**The key may have been exposed before removal.** If this repo was ever cloned, forked, or pushed to a remote, the key exists in those copies.

### Action Required

1. **Generate a new RSA key pair:**
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/ettametta_new -N ""
   ```

2. **Revoke the old key** from any services that used it (GitHub deploy keys, server SSH access, etc.)

3. **Deploy the new key** to all services

4. **Update `.env`** with the new key path if applicable

## GitHub Token Exposure

The `git filter-repo` operation revealed that the git remote URL contained a GitHub personal access token (`ghp_...`). This token was in the git config, not in tracked files.

### Action Required

1. **Revoke the token** at https://github.com/settings/tokens
2. **Generate a new token** if needed
3. **Re-add the remote** with the new token or use SSH:
   ```bash
   git remote add origin git@github.com:psalmprax/ettametta.git
   ```

## Summary of Removed Files

The following were purged from git history:
- `key_raw.txt` — RSA private key
- `*.db` — SQLite database files (10+ files)
- `*.tar.gz` — Patch archives (12 files)
- `.kilo/` — AI tool state
- `.kilocode/` — AI tool state
- `GitNexus` — External tool reference

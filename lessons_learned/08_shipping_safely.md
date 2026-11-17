# 8. Shipping safely: secrets, history and the pre-push gate

**Public repo:** this course, [day16_security/secrets_scan.py](../day16_security/secrets_scan.py) (a secrets
scanner that runs in CI) and [day11_git_docker/](../day11_git_docker/) (Git and CI).

## The problem

A secret removed from the code is not removed from the repo. Git keeps every old version. Anyone who can clone
the repo can read the history.

## What went wrong

- **Keys in old history.** When I prepared older work for a public repo, the current files were clean, but a
  market-data API key was still in an early commit. Deleting the line had only hidden it.
- **Other things that should never leave a laptop**: real names in comments, absolute local paths, and data
  files that were not mine to share.
- **Printing env values "safely".** Printing only variables whose name contains `URL` sounds harmless. But a
  database URL embeds the password (`user:password@host`), so the filter printed a secret.
- **Trusting "it passed locally".** A push is not done until the real CI run on the server is green.

## The fix

- **Rotate first.** A key that was ever pushed is burned. I rotated it before anything else. Rewriting history
  is the second step, not the fix.
- **Start public repos from clean history** (or rewrite it), then scan the whole history, not just the tip.
- **Secrets live in the environment or a secret manager**, never in code, notebooks or example configs.
  `.gitignore` covers `.env`, data folders and output folders from the first commit.
- **A pre-push gate** that fails on: names on a deny list, secret patterns (keys, tokens, private keys), absolute
  local paths and email addresses, and data files by extension and size.
- **Print env names, never values.** Check that a variable is set; do not echo it.
- **Check the real CI after every push**, and explain every non-green check before moving on.

## How to spot it next time

- `git log -p` or a history scanner finds a pattern that the current files do not have.
- A config example holds a real-looking value instead of a placeholder.
- A debug line prints environment variables, even filtered ones.
- A large `.csv` or `.parquet` file is staged.
- "CI is green" was said without opening the run.

## Say it in an interview

> I was making old work public, and the files looked clean.
> But an API key was still in an early commit, because deleting a line does not delete history.
> I rotated the key first, then published from clean history and scanned all of it.
> Now a pre-push gate checks for secrets, names, local paths and data files, and I check real CI after every push.
> The gate only catches patterns it knows, so rotation and review still matter.

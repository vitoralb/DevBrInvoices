# Cherry-Pick & Release Workflow Guide

This guide establishes the branch management and release workflow for the `notas` repository, detailing the dual-branch strategy between `dev` and `master`, known divergences, and the step-by-step procedure for safely cherry-picking features and bugfixes into production.

---

## 1. Branch Roles & Architecture

- **`dev` branch**:
  - **Purpose**: Active feature development, experimentation, and Sefin Nacional Homologação / RTC 1.6.0 testing.
  - **Stability**: Rapidly evolving, contains cutting-edge schemas, experimental tax structures (CBS/IBS), and preview APIs.
  - **Environment**: Serves as the base for active development containers (`make dev-spawn BIND=1`).

- **`master` branch**:
  - **Purpose**: Stable production code deployed to the live production stack (`notas-web-1`, `notas-db-1`, etc.).
  - **Stability**: Highly stable, battle-tested, strictly matching live production Prefeitura and Sefin Produção APIs.
  - **Deployment**: Only code committed to `master` may be deployed to production via `make prod-upgrade`.

---

## 2. Permanent / Known File Divergences

The following files on `dev` contain Sefin Nacional RTC 1.6.0 schema compliance and must **NOT** be blindly merged into `master` until Sefin Nacional RTC is formally promoted in Production:

1. `core/nfse/nacional/schemas/v1_01/tipos_complexos_v1_01.py` (RTC 1.6.0 DPS complex types)
2. `core/nfse/nacional/provider.py` (RTC 1.6.0 provider payload structures)
3. `core/tests/test_cbs_ibs.py` (RTC 1.6.0 CBS/IBS unit tests)
4. `core/nfse/nacional/xsd/esquemas-nfse-rtc-v1-01-20260727/` (Offline reference XSD schemas for RTC)

---

## 3. Step-by-Step Cherry-Pick Procedure

When a feature, fix, or improvement developed on `dev` (or an `agent-*` branch off `dev`) needs to be released to production (`master`), follow this exact protocol:

### Step 1: Identify the Specific Commits on `dev`
Locate the commit hash(es) on `dev` containing the intended changes:
```bash
git log dev -n 10 --oneline
```

### Step 2: Switch to `master` and Ensure Clean Working Tree
```bash
git checkout master
git status
```
Verify that the working tree is clean.

### Step 3: Cherry-Pick the Target Commit(s)
```bash
git cherry-pick <commit-hash>
```

If merge conflicts occur in any of the known divergent files (`core/nfse/nacional/provider.py`, etc.):
- Resolve conflicts carefully by keeping the production-compatible stable code on `master`.
- Run `git status` and `git diff` to confirm only the intended changes are staged.
- Complete the cherry-pick:
  ```bash
  git cherry-pick --continue
  ```

### Step 4: Verify via a Reference Dev Stack on `master`
Before upgrading production, spawn a reference dev instance on `master` to run the test suite and verify stability in an isolated environment:
```bash
# 1. Spawn isolated dev container on port 8082 pointing to master
make dev-spawn PORT=8082 REF=master

# 2. Run the test suite against this dev instance
make dev-test PORT=8082

# 3. Destroy the verification container when done
make dev-destroy PORT=8082
```

### Step 5: Upgrade Production
Once verified on `master`:
```bash
make prod-upgrade
```
This rebuilds the production Docker image, restarts production containers, and executes pending migrations and `collectstatic`.

### Step 6: Return to `dev` for Continued Development
```bash
git checkout dev
```

---

## 4. Strict Golden Rules for AI Agents

1. **NEVER Execute `git push` Without Explicit User Instruction**:
   - Neither on `master` nor on `dev`.
   - Never push automatically; always wait for explicit instruction from the user.

2. **Never Run Tests on Production**:
   - Tests must strictly run inside development containers (`make dev-test`).

3. **Preserve Divergent Files**:
   - Never run `git merge dev` into `master` without filtering out or resolving the RTC 1.6.0 divergences. Always prefer cherry-picking targeted commits.

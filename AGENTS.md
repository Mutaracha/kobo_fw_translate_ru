# Agent instructions — kobalt_ru
## Environment and recovery
Arena is Linux. Recheck`command -v git gh cmake qmake docker jq` each session. Do not assume a Qt SDK orcontainer engine exists. Local offline checks cannot replace native/Qt5 CI.Never introduce Python into CMake or application build dependencies.
Files and Git metadata can be restored independently: HEAD may return to thesession base while files reflect later pushed work. Inspect `git status -sb`,`git log -5 --oneline`, fetch the assigned branch and compare file contents toits remote tree before editing/committing. Do not blindly commit the wholeapparent delta or discard it. If justified by inspection, align only the index/branch with a mixed reset, preserving working files; an isolated index based onthe remote tree can publish an explicit file list without staging unrelated data.Never use a hard reset as recovery. Confirm the remote result after publishing.
Scratch files, `/tmp` uploads and excluded directories such as `.arena`/`.cache`may disappear across turns. Do not rely on them for handoff evidence; preserverequested deliverables and original uploads in their documented locations.Large generated artifacts/builds do not belong in Git. Do not repeat unchangedcommands after timeout; use managed process tools for CI watches/servers.

## Translation work
Follow the [firmware translation guidelines](TRANSLATION.md) when editing or reviewing catalogs.

## Repository layout and note placement
- `src/<version>/` holds the English source catalogs for that firmware. Extract `nickel` in temporary storage. Remove offset-named QM candidates only after the English QM/TS pair has been saved. The original 4.38.23852 English catalogs are directly under `src/`.
- `translated/<version>/` is for `trans_ru.ts` and `trans_ru.qm` only. Do not create notes, screenshots, archives, backups, or temporary build outputs anywhere in `translated/`.
- Keep generated untranslated-string and length reports in the ignored `reports/<version>/` directory, outside the catalogs.
- `py_script/` contains catalog tools and the Windows launcher; `tests/` contains offline tests. `scripts/` and `.github/workflows/` handle packaging. `patch/` holds installable fonts and hyphenation data. Publish `KoboRoot.tgz` as an Actions artifact, not a repository file.
- Keep the font-removal script and its udev rule in `reference/legacy-scripts/` for reference only. Do not run or package them. Document their purpose in that directory's README.
- Put user-facing setup, build, and installation instructions in `README.md`. Put reusable terminology and translation QA rules in `TRANSLATION.md`. Keep `AGENTS.md` in English and limit it to durable workflow instructions and verified environment caveats.
- Record version-specific review findings and screenshot feedback in the relevant issue or pull request. Keep one-off comparison tables and test output out of Git; summarize reusable guidance in the appropriate document above.

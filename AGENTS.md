# Agent instructions — kobalt_ru
## Environment and recovery
Arena is Linux. Recheck`command -v git gh cmake qmake docker jq` each session. Do not assume a Qt SDK orcontainer engine exists. Local offline checks cannot replace native/Qt5 CI.Never introduce Python into CMake or application build dependencies.
Files and Git metadata can be restored independently: HEAD may return to thesession base while files reflect later pushed work. Inspect `git status -sb`,`git log -5 --oneline`, fetch the assigned branch and compare file contents toits remote tree before editing/committing. Do not blindly commit the wholeapparent delta or discard it. If justified by inspection, align only the index/branch with a mixed reset, preserving working files; an isolated index based onthe remote tree can publish an explicit file list without staging unrelated data.Never use a hard reset as recovery. Confirm the remote result after publishing.
Scratch files, `/tmp` uploads and excluded directories such as `.arena`/`.cache`may disappear across turns. Do not rely on them for handoff evidence; preserverequested deliverables and original uploads in their documented locations.Large generated artifacts/builds do not belong in Git. Do not repeat unchangedcommands after timeout; use managed process tools for CI watches/servers.

## Translation work
Follow the [firmware translation guidelines](TRANSLATION.md) when editing or reviewing catalogs.

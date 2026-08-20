# Release and archival process

1. Resolve release-blocking issues and update the changelog, version, citation
   metadata, documentation, and supported-version policy.
2. Run lint, formatting, typing, tests with coverage, wheel/sdist build, and
   `twine check` in a clean environment.
3. Confirm the JOSS paper builds and references resolve.
4. Create a signed or annotated semantic-version tag from the reviewed commit.
5. Publish the GitHub release and package artifact when package-index publishing
   is enabled.
6. Archive that exact tag with Zenodo, verify title/authors/license, and record
   the DOI in `CITATION.cff` and the JOSS review thread.
7. Do not rewrite or reuse released tags. Patch errors in a new release.

The first archival DOI requires repository-owner action and cannot be created by
an automated code change without explicit publishing authorization.


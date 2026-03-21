# GitHub Pages

This repository serves the latest EPG XMLTV file via GitHub Pages.

- The EPG is updated daily by a GitHub Actions workflow.
- The file is available at: `https://muq-org.github.io/tv-epg/epg.xml`

## Setup

1. Enable GitHub Pages in the repository settings:
   - Source: **GitHub Actions**
2. The workflow `.github/workflows/update-epg.yml` will generate and deploy `epg.xml` daily.
3. The file will be available at the above URL after the first workflow run.

## Notes
- `epg.xml` is not committed to the repository — it is generated and deployed entirely in CI.
- `.nojekyll` is included to ensure the XML file is served as-is.

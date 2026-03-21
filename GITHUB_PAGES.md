# GitHub Pages

This repository is configured to serve the latest EPG XMLTV file via GitHub Pages.

- The file `epg.xml` is updated daily by a GitHub Actions workflow.
- The file is available at: `https://<your-username>.github.io/<repo-name>/epg.xml`
- `.nojekyll` is included to ensure the XML file is served as-is.

## Setup

1. Enable GitHub Pages in the repository settings:
   - Source: `main` branch, root (`/`)
2. The workflow `.github/workflows/update-epg.yml` will update and commit `epg.xml` daily.
3. The file will be available at the above URL after the first workflow run.

## Security
- Do not commit secrets or API keys to the repository.
- Use repository secrets for sensitive data if needed.

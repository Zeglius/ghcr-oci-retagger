# ghcr-oci-retagger

Retag multiple images by tag with skopeo.

## Inputs

| **Input name** | **Description**                                                                                          | **Default** | **Required** |
| -------------- | -------------------------------------------------------------------------------------------------------- | ----------- | ------------ |
| TAG_MAPPINGS   | String of image mappings in the form of 'src_img:src_tag => dst_img:dst_img' delimited by newlines       | None        | Yes          |
| PREFIX         | Prepend a string to image references. Used to avoid repeating registry domain (ex.: `ghcr.io/ublue-os/`) | None        | No           |
| SRC_PREFIX     | Prepend a string to source image references. Overrides PREFIX                                            | None        | No           |
| DST_PREFIX     | Prepend a string to destination image references. Overrides PREFIX                                       | None        | No           |
| GITHUB_TOKEN   | Github token with packages:write permission                                                              | None        | Yes          |

## Examples

### Manual trigger

```yaml
# yaml-language-server: $schema=https://json.schemastore.org/github-workflow.json

name: Retag image

concurrency:
  group: ${{ github.workflow }}
  cancel-in-progress: true

permissions:
  packages: write

on:
  workflow_dispatch:
    inputs:
      old_tag:
        description: "Old tag from which images will be retagged to latest"
        required: true
        type: string

jobs:
  safeguard-timer:
    runs-on: ubuntu-latest
    if: inputs.old_tag != ''
    steps:
      - name: Safeguard wait
        env:
          SLEEP_TIME: "30"
        run: |
          echo "Triggered safeguard."
          echo "You have $SLEEP_TIME seconds to cancel the workflow if you want to cancel retagging."
          sleep $SLEEP_TIME

  retag-images:
    runs-on: ubuntu-latest
    needs: [safeguard-timer]
    if: inputs.old_tag != ''
    steps:
      - uses: Zeglius/ghcr-oci-retagger@3d5fa57743ba2a94b125317aee52f0daf8743d12
        with:
          GITHUB_TOKEN: ${{ github.token }}
          PREFIX: ghcr.io/
          TAG_MAPPINGS: |-
            ${{ github.repository }}:${{ inputs.old_tag }} => ${{ github.repository }}:latest
```

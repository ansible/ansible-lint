# meta-video-links

This rule checks formatting for video links in metadata. Always use dictionaries
for items in the `meta/main.yml` file.

Items in the `video_links` section must be in a dictionary and use the following
keys:

- `url`
- `title`

The value of the `url` key must be a shared link from YouTube, Vimeo, or Google
Drive.

## Problematic Code

```yaml
---
galaxy_info:
  video_links:
    - https://www.youtube.com/watch?v=aWmRepTSFKs&feature=youtu.be # <- Does not use the url key.
    - my_bad_key: https://www.youtube.com/watch?v=aWmRepTSFKs&feature=youtu.be # <- Uses an unsupported key.
      title: Incorrect key.
    - url: www.acme.com/vid # <- Uses an unsupported url format.
      title: Incorrect url format.
```

## Correct Code

```yaml
---
galaxy_info:
  video_links:
    - url: https://www.youtube.com/watch?v=aWmRepTSFKs&feature=youtu.be # <- Uses a supported shared link with the url key.
      title: Correctly formatted video link.
```

# Glance dashboard (Plant Tracker)

This project already exposes the latest readings through the FastAPI endpoints:

- `GET /health`
- `GET /devices/latest`
- `GET /devices/{device}/latest`

Glance can display these JSON payloads using the **`custom-api`** widget (template-driven).

## Example `glance.yml` snippet

Set an environment variable that points to your Plant Tracker API (running on the ZimaBoard):

- `PLANT_TRACKER_URL=http://ZIMABOARD_IP:8000`

Then add a widget like this:

```yaml
pages:
  - name: Plant Tracker
    columns:
      - size: full
        widgets:
          - type: custom-api
            title: Sensors (latest)
            cache: 30s
            url: ${PLANT_TRACKER_URL}/devices/latest
            template: |
              {{/*
                Expects Plant Tracker payload:
                {
                  "devices": [
                    {"device":"plant_1","time":"...","fields":{"temperature":21.5, ...}},
                    ...
                  ]
                }
              */}}

              <ul class="list list-gap-10 collapsible-container" data-collapse-after="8">
                {{ range .JSON.Array "devices" }}
                  {{ $name := .String "device" }}
                  {{ $time := .String "time" }}

                  <li class="flex justify-between gap-15">
                    <div class="min-width-0">
                      <div class="size-h4 color-highlight text-truncate">{{ $name }}</div>
                      {{ if $time }}
                        <div class="size-h6 color-paragraph">{{ $time }}</div>
                      {{ else }}
                        <div class="size-h6 color-paragraph">no data yet</div>
                      {{ end }}
                    </div>

                    <ul class="list-horizontal-text">
                      <li>
                        <span class="color-paragraph">fields</span>
                        <span class="color-highlight">{{ .Get "fields" }}</span>
                      </li>
                    </ul>
                  </li>
                {{ end }}
              </ul>
```

### Notes / troubleshooting

- Glance fetches the URL **from the machine where Glance runs**. If Glance is in Docker, the URL must be reachable from that container.
  - If Glance runs on the **same ZimaBoard Docker network**, you can also point it to `http://plant-tracker-app:8000` (service name) instead of the LAN IP.
- If you have multiple pages, consider using `$include` in Glance config to keep this widget in its own file.
- If a field is missing for a device, the template simply hides that value.


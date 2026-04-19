# Open Wearables iOS

Minimum-viable iOS client: redeem an invitation code, view a 14-day daily frame
(sleep score, heart rate, eating events, habits).

## Prerequisites

- macOS with Xcode 15+
- [XcodeGen](https://github.com/yonaskolb/XcodeGen): `brew install xcodegen`
- Backend running locally: `docker compose up -d` from the repo root

## Quick start

```bash
cd ios
make run          # generates .xcodeproj and opens Xcode
# Select an iPhone simulator → Cmd+R
```

Or build from the CLI:

```bash
make build
make test
```

## First-run setup

The app authenticates via invitation codes. To get one:

```bash
# 1. Create a user (admin)
curl -s -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_jwt>" \
  -d '{"first_name": "Test"}' | jq

# 2. Generate an invitation code
curl -s -X POST http://localhost:8000/api/v1/users/<user_id>/invitation-code \
  -H "Authorization: Bearer <admin_jwt>" | jq '.code'
```

Paste the 8-character code into the app's onboarding screen.

## Configuration

`API_BASE_URL` defaults to `http://localhost:8000` in Debug builds.
Override it in `project.yml` under `configs.Release` for production.

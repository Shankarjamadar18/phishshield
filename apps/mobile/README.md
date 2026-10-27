# PhishShield mobile (Flutter)

Phase 1 skeleton: calls `GET /health` on the shared backend. **Not built or tested** — Flutter isn't available in the Lovable environment.

```bash
cd apps/mobile
flutter create . --project-name phishshield_mobile   # generates android/ios folders
flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:8000
```

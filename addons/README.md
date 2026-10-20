Place addon checkouts here (ignored by Git), or mount them from elsewhere.
Copy compose.addon.example.yaml to compose.override.yaml, then customize its build
context and environment. The controller automatically includes that override.
The application is reachable by its Compose service name; localhost inside an
addon points at that addon. Credentials are in /runtime/credentials.json.
Use a separate project name and different ports in .env for parallel instances.

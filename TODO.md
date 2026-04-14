# Frontend React npm install fix TODO

## Plan Steps:
1. [ ] Kill Node/npm processes (taskkill /f /im node.exe /t && taskkill /f /im npm.exe /t)
2. [ ] cd frontend-react && rmdir /s /q node_modules 2>nul
3. [ ] npm cache clean --force
4. [ ] npm install
5. [ ] Verify: ls node_modules/react && npm run dev

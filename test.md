# PowerShell Test Commands

Use these commands from:

```powershell
C:\Users\sruja\Documents\vscodeex
```

Make sure the backend server is running first.

## 1. Health Check

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get
```

## 2. Ask The Agent To Create A Python File

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "Create a Python file named app.py that prints Hello, World!"}'
```

## 3. Break `app.py` Manually

```powershell
Set-Content -Path ".\backend\workspace\app.py" -Value "print('Hello, World!'),."
```

## 4. Ask The Agent To Fix The Broken File

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "Fix the code in app.py"}'
```

## 5. Check The Fixed File

```powershell
Get-Content ".\backend\workspace\app.py"
```

## 6. Check The Generated Test File

```powershell
Get-Content ".\backend\workspace\tests\test_app.py"
```

## 7. Run The Generated Tests Manually

```powershell
Set-Location ".\backend\workspace"
python -m unittest discover -s tests -p "test_*.py" -v
Set-Location "..\.."
```

## 8. Ask The Agent To Create A Calculator File

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "Create a Python calculator in calc.py with add, subtract, multiply, and divide functions, then validate it"}'
```

## 9. Inspect The Generated Calculator File

```powershell
Get-Content ".\backend\workspace\calc.py"
```

## 10. Inspect The Generated Calculator Tests

```powershell
Get-Content ".\backend\workspace\tests\test_calc.py"
```

## 11. Run All Workspace Tests

```powershell
Set-Location ".\backend\workspace"
python -m unittest discover -s tests -p "test_*.py" -v
Set-Location "..\.."
```

## 12. Force Another Broken Example

```powershell
Set-Content -Path ".\backend\workspace\calc.py" -Value @"
def add(x, y)
    return x + y
"@
```

## 13. Ask The Agent To Repair The Broken Calculator

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "Fix the code in calc.py"}'
```

## 14. Read The Final Calculator Code

```powershell
Get-Content ".\backend\workspace\calc.py"
```

## 15. Read The Final Calculator Tests

```powershell
Get-Content ".\backend\workspace\tests\test_calc.py"
```

## Optional: Full Manual Flow In One Go

```powershell
Set-Content -Path ".\backend\workspace\app.py" -Value "print('Hello, World!'),."

Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "Fix the code in app.py"}'

Get-Content ".\backend\workspace\app.py"
Get-Content ".\backend\workspace\tests\test_app.py"

Set-Location ".\backend\workspace"
python -m unittest discover -s tests -p "test_*.py" -v
Set-Location "..\.."
```

## Notes

- If the responses still look old, restart the FastAPI server before testing.
- All generated code and tests are stored under `backend\workspace`.
- The generated test files should appear under `backend\workspace\tests`.

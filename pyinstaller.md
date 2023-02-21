## Taskbar Icons

Unfortunately, even if the icon is showing on the window, it may still not show on the taskbar.

```python
try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'com.mycompany.myproduct.subproduct.version'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass
```
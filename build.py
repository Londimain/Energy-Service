"""
Сборка exe через PyInstaller.

Использование:
    python build.py

Файл version_info.txt автоматически перегенерируется на основе version.py,
что гарантирует единую версию во всех файлах (окно, exe, свойства файла).
"""
import os
import sys
import subprocess

from version import VERSION, APP_NAME


VERSION_INFO_TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={filevers},
    prodvers={prodvers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [StringStruct('CompanyName', 'Energy'),
           StringStruct('FileDescription', '{app_name}'),
           StringStruct('FileVersion', '{version}'),
           StringStruct('InternalName', '{internal_name}'),
           StringStruct('LegalCopyright', ''),
           StringStruct('OriginalFilename', '{exe_name}'),
           StringStruct('ProductName', '{app_name}'),
           StringStruct('ProductVersion', '{version}')]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def generate_version_info():
    parts = VERSION.split('.')
    while len(parts) < 4:
        parts.append('0')
    try:
        version_tuple = tuple(int(p) for p in parts[:4])
    except ValueError:
        version_tuple = (0, 0, 0, 0)
    version_str = '.'.join(str(p) for p in version_tuple)

    content = VERSION_INFO_TEMPLATE.format(
        filevers=version_tuple,
        prodvers=version_tuple,
        app_name=APP_NAME,
        version=version_str,
        internal_name=APP_NAME.replace(' ', ''),
        exe_name=APP_NAME.replace(' ', '') + '.exe',
    )
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"version_info.txt обновлён: v{version_str}")


def build():
    generate_version_info()
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm',
        '--clean',
        '--onefile',
        '--windowed',
        '--name', 'EnergyReport',
        '--icon', 'ico/appEnergy.ico',
        '--add-data', 'ico;ico',
        '--version-file', 'version_info.txt',
        'main.py',
    ]
    print("Запуск:", " ".join(cmd))
    subprocess.check_call(cmd)


if __name__ == "__main__":
    build()
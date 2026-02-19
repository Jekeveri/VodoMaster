; Название установщика
OutFile "VodoMaster_Installer.exe"

; Папка установки по умолчанию
InstallDir "$LOCALAPPDATA\VodoMaster"

; Иконка установщика
!define MUI_ICON "C:\Users\1\Desktop\windsurf 27.6\images\logoWinInstaller.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Подключение Modern UI
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinMessages.nsh"
!include "Win\COM.nsh"
!include "WinCore.nsh"
!include x64.nsh

; Версия приложения
!define PRODUCT_NAME "Vodo Master"
!define PRODUCT_VERSION "1.2.0.1"
!define PKGDIR "C:\Users\1\Desktop\windsurf 27.6\dist\Vodo Master"

VIProductVersion "1.2.0.1"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "LegalCopyright" "© 2025 МП Трест Водоканал МО г.Магнитогорск. Все права защищены."
VIAddVersionKey "FileDescription" "Установочный пакет VodoMaster"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"

; Настройки реестра
!define HKLM_ENV 'HKLM "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"'
!define HKLM_SOFT 'HKLM "Software\VodoMaster"'

; Типы установки
InstType "Полная"
InstType "Минимальная"

; Настройки интерфейса
!define MUI_ABORTWARNING
!define MUI_COMPONENTSPAGE_SMALLDESC

; Страницы установщика
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Страницы удаления
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Язык
!insertmacro MUI_LANGUAGE "Russian"

RequestExecutionLevel user

Name "${PRODUCT_NAME}"
Caption "Установка ${PRODUCT_NAME} ${PRODUCT_VERSION}"
ShowInstDetails show

Var CREATESHORTCUTS
Var INSTALLED_VERSION
Var NEW_VERSION

; Кастомная функция сравнения версий
Function CompareVersions
  Exch $NEW_VERSION ; Новая версия (версия установщика)
  Exch
  Exch $INSTALLED_VERSION ; Установленная версия
  Push $0
  Push $1
  Push $2
  Push $3
  Push $4
  Push $5
  Push $6

  ; Разбиваем установленную версию на компоненты
  StrCpy $0 0 ; Результат сравнения
  StrCpy $1 0 ; Индекс для $INSTALLED_VERSION
  StrCpy $2 0 ; Индекс для $NEW_VERSION

  loop_installed:
    StrCpy $3 $INSTALLED_VERSION 1 $1
    ${If} $3 == "."
    ${OrIf} $3 == ""
      StrCpy $4 $INSTALLED_VERSION $1
      IntOp $1 $1 + 1
      StrCpy $INSTALLED_VERSION $INSTALLED_VERSION "" $1
      Goto loop_new
    ${Else}
      IntOp $1 $1 + 1
      Goto loop_installed
    ${EndIf}

  loop_new:
    StrCpy $5 $NEW_VERSION 1 $2
    ${If} $5 == "."
    ${OrIf} $5 == ""
      StrCpy $6 $NEW_VERSION $2
      IntOp $2 $2 + 1
      StrCpy $NEW_VERSION $NEW_VERSION "" $2
      Goto compare
    ${Else}
      IntOp $2 $2 + 1
      Goto loop_new
    ${EndIf}

  compare:
    ; Преобразуем $4 и $6 в числа
    IntOp $4 $4 + 0
    IntOp $6 $6 + 0

    ${If} $4 > $6
      StrCpy $0 1 ; Установленная версия новее
      Goto end
    ${ElseIf} $4 < $6
      StrCpy $0 -1 ; Новая версия новее
      Goto end
    ${EndIf}

    ${If} $INSTALLED_VERSION == ""
    ${AndIf} $NEW_VERSION == ""
      StrCpy $0 0 ; Версии равны
      Goto end
    ${EndIf}

    StrCpy $1 0
    StrCpy $2 0
    Goto loop_installed

  end:
    Pop $6
    Pop $5
    Pop $4
    Pop $3
    Pop $2
    Pop $1
    Exch $0
FunctionEnd

 Var MYVAR0
 Var MYVAR1
 Var MYVAR2

Function .onInit
 ${If} ${RunningX64}
    SetRegView 64
  ${Else}
    SetRegView 32
  ${EndIf}

  ; Чтение установленной версии и пути установки
  ReadRegStr $MYVAR0 HKLM "Software\VodoMaster" "InstallPath"
  ReadRegStr $MYVAR1 HKLM "Software\VodoMaster" "Version"

  ${If} $MYVAR0 != ""
  ${AndIf} $MYVAR1 != ""
    ; Сохраняем установленную версию в $MYVAR1
    Push $MYVAR1 ; Установленная версия
    Push "${PRODUCT_VERSION}" ; Новая версия
    Call CompareVersions
    Pop $MYVAR2 ; Результат: 1 (уст. новее), -1 (новая новее), 0 (равны)

    ${Switch} $MYVAR2
      ${Case} -1
        MessageBox MB_YESNO|MB_ICONQUESTION "Обнаружена старая версия $MYVAR1. Установить новую ${PRODUCT_VERSION}?" IDYES proceed
        Abort

      ${Case} 1
        MessageBox MB_OK|MB_ICONSTOP "Установленная версия $MYVAR1 новее. Отмена установки."
        Abort

      ${Case} 0
        MessageBox MB_YESNO|MB_ICONQUESTION "Версия $MYVAR1 уже установлена. Переустановить?" IDYES proceed
        Abort
    ${EndSwitch}
  ${EndIf}

  proceed:
FunctionEnd

Section -PreInstallChecks
  ${If} ${RunningX64}
    SetRegView 64
  ${EndIf}

  System::Call 'kernel32::CreateMutexA(i 0, i 0, t "VodoMasterMutex") i .r1 ?e'
  Pop $0
  StrCmp $0 0 +3
    MessageBox MB_OK|MB_ICONSTOP "Установщик уже запущен!"
    Abort
SectionEnd

Section "-Prerequisites"
  ; Проверка 32-битных DLL
  IfFileExists "$WINDIR\SysWOW64\vcruntime140.dll" vc_installed
    ; Скачивание vcredist если не найден
    NSISdl::download "https://aka.ms/vs/17/release/vc_redist.x86.exe" "$PLUGINSDIR\vc_redist.x86.exe"
    Pop $0
    StrCmp $0 "success" dl_ok
      MessageBox MB_OK|MB_ICONEXCLAMATION "Не удалось скачать Visual C++ Redistributable. Программа может не работать корректно."
      Goto vc_installed
    dl_ok:
    ExecWait '"$PLUGINSDIR\vc_redist.x86.exe" /install /quiet /norestart'
    Delete "$PLUGINSDIR\vc_redist.x86.exe"
  vc_installed:
SectionEnd

Section "!Основные компоненты" secMain
  SectionIn 1 2 RO
  SetOutPath "$INSTDIR"

  File /r /x "*.pyc" /x "__pycache__" "${PKGDIR}\*.*"
  File /r /x "VodoMaster_Installer.exe" "${PKGDIR}\*.*"

  ${IfNot} ${FileExists} "$SYSDIR\vcruntime140.dll"
    DetailPrint "Установка Visual C++ Redistributable..."
    NSISdl::download "https://aka.ms/vs/17/release/vc_redist.x86.exe" "$PLUGINSDIR\vc_redist.x86.exe"
    Pop $R0
    ${If} $R0 == "success"
      ExecWait '"$PLUGINSDIR\vc_redist.x86.exe" /install /quiet /norestart'
      Delete "$PLUGINSDIR\vc_redist.x86.exe"
    ${Else}
      MessageBox MB_OK|MB_ICONEXCLAMATION "Не удалось скачать VC++ Redist. Программа может не работать!"
    ${EndIf}
  ${EndIf}

  ; Запись в реестр
   ${If} ${RunningX64}
    SetRegView 64 ; Явно указываем для 64-битных систем
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\VodoMaster" "InstallPath" "$INSTDIR"
  ${Else}
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster" "DisplayName" "${PRODUCT_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\VodoMaster" "InstallPath" "$INSTDIR"
  ${EndIf}

  WriteRegStr HKLM "Software\VodoMaster" "Version" "${PRODUCT_VERSION}"

  WriteRegStr ${HKLM_SOFT} "InstallPath" "$INSTDIR"
  WriteRegStr ${HKLM_SOFT} "Version" "${PRODUCT_VERSION}"
  WriteRegStr ${HKLM_SOFT} "" "$INSTDIR"

  Call CheckRequiredDLLs
SectionEnd

Function CheckRequiredDLLs
  ; Список необходимых DLL
  StrCpy $0 0 ; Счетчик отсутствующих DLL

  ; Проверка наличия DLL в системных директориях
  ${IfNot} ${FileExists} "$SYSDIR\vcruntime140.dll"
    IntOp $0 $0 + 1
    StrCpy $1 "vcruntime140.dll"
  ${EndIf}

  ${IfNot} ${FileExists} "$SYSDIR\msvcp140.dll"
    IntOp $0 $0 + 1
    StrCpy $2 "msvcp140.dll"
  ${EndIf}

  ; Если есть отсутствующие DLL, предлагаем скачать
  ${If} $0 > 0
    MessageBox MB_YESNO|MB_ICONQUESTION "Для работы программы необходимы следующие DLL:$\n$\n\
      $1$\n$2$\n$3$\n$\nСкачать их автоматически? (Рекомендуется)" IDNO noDownload

    ; Создаем папку для зависимостей
    SetOutPath "$INSTDIR\_internal\dll"

    ; Скачивание VC++ Redist DLL
    ${IfNot} ${FileExists} "$SYSDIR\vcruntime140.dll"
      NSISdl::download "https://example.com/path/to/vcruntime140.dll" "$INSTDIR\_internal\dll\vcruntime140.dll"
      Pop $R0
      StrCmp $R0 "success" +2
        DetailPrint "Ошибка загрузки vcruntime140.dll"
    ${EndIf}

    ${IfNot} ${FileExists} "$SYSDIR\msvcp140.dll"
      NSISdl::download "https://example.com/path/to/msvcp140.dll" "$INSTDIR\_internal\dll\msvcp140.dll"
      Pop $R0
      StrCmp $R0 "success" +2
        DetailPrint "Ошибка загрузки msvcp140.dll"
    ${EndIf}

    ; Добавляем путь к DLL в переменную PATH
    ; (или копируем в системную директорию с согласия пользователя)
    MessageBox MB_YESNO|MB_ICONQUESTION "Скопировать DLL в системную директорию?$\n$\n\
      (Требуются права администратора)" IDNO noCopyToSystem
      CopyFiles "$INSTDIR\_internal\dll\*.dll" "$SYSDIR"
    noCopyToSystem:

    noDownload:
  ${EndIf}
FunctionEnd

Section "-Завершение"
  MessageBox MB_OK "Установка завершена успешно!"
SectionEnd

SectionGroup "Ярлыки" grpShortcuts
  Section "В меню Пуск"
    SectionIn 1
    SetShellVarContext all
    CreateDirectory "$SMPROGRAMS\VodoMaster"
    CreateShortcut "$SMPROGRAMS\VodoMaster\VodoMaster.lnk" "$INSTDIR\Vodo Master.exe" "" "$INSTDIR\_internal\images\logoWin.ico"
    StrCpy $CREATESHORTCUTS "true"
  SectionEnd

  Section "На рабочем столе"
    SectionIn 1
    CreateShortcut "$DESKTOP\VodoMaster.lnk" "$INSTDIR\Vodo Master.exe" "" "$INSTDIR\_internal\images\logoWin.ico"
  SectionEnd
SectionGroupEnd

Section "-Создание деинсталлятора"
  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Секция удаления
Section "Uninstall"
  ; Удаление файлов
  RMDir /r "$INSTDIR"

  ; Удаление ярлыков
  Delete "$DESKTOP\VodoMaster.lnk"
  RMDir /r "$SMPROGRAMS\VodoMaster"

  ${If} ${RunningX64}
    SetRegView 64 ; Указываем 64-битный режим для 64-битных систем
    DetailPrint "Удаление ключа реестра (64-бит): Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster"
    DetailPrint "Удаление ключа реестра (64-бит): Software\VodoMaster"
    DeleteRegKey HKLM "Software\VodoMaster"
    DetailPrint "Удаление значения переменной окружения (64-бит): VodoMaster_Path"
    DeleteRegValue ${HKLM_ENV} "VodoMaster_Path"
   ${Else}
    SetRegView 32 ; Указываем 32-битный режим для 32-битных систем
    DetailPrint "Удаление ключа реестра (32-бит): Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\VodoMaster"
    DetailPrint "Удаление ключа реестра (32-бит): Software\VodoMaster"
    DeleteRegKey HKLM "Software\VodoMaster"
    DetailPrint "Удаление значения переменной окружения (32-бит): VodoMaster_Path"
    DeleteRegValue ${HKLM_ENV} "VodoMaster_Path"
   ${EndIf}
SectionEnd

; Описания компонентов
LangString DESC_secMain ${LANG_RUSSIAN} "Основные компоненты программы, необходимые для работы"
LangString DESC_grpShortcuts ${LANG_RUSSIAN} "Создание ярлыков для быстрого доступа"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${secMain} $(DESC_secMain)
  !insertmacro MUI_DESCRIPTION_TEXT ${grpShortcuts} $(DESC_grpShortcuts)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
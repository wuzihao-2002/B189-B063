# GoogleDriveResearchTool
GoogleDrive調査ツール。

## ビルド環境
    開発言語　　　　　　　　　　  :Python
    開発ツール             　 　:JetBrains PyCharm Community Edition 2019.1.3 x64
    フレームワーク             　:Python 3.8.4 x64
    プラットフォームターゲット	    :x64

## 動作環境(Windows10 64bit)

## フォルダ構造
    ..\ツール
    ├ GoogleDriveResearchTool.exe            :本ツールの本体EXE
	├ GoogleDriveResearchTool.bat            :EXE起動BAT
    ├ GoogleDriveResearchTool.yaml           :配置ﾌｧｲﾙ（本ツール用）
    ├ AuthenticationConfig                   :暗号化済みの認証ﾌｧｲﾙ保存用
	│├ settings.yaml                         :下記必要なﾌｧｲﾙのバス設定用	
	│├ saved_credentials.json				 :Googleｱｶｳﾝﾄ認証ﾌｧｲﾙ
	│├ privatekey_saved_credentials.bin      :Googleｱｶｳﾝﾄ認証ﾌｧｲﾙ復号化処理用キー

## 使い方
本ツールの本体は **GoogleDriveResearchTool.exe** です。  
**GoogleDriveResearchTool.bat** から調査ツールを起動する。   
ﾌｧｲﾙ「**GoogleDrive調査ツール_使用説明.xlsx**」を参照する。    
"""Scaffolds a turnkey Unreal Engine 5 C++ Plugin for OpenLore Live Link."""

from __future__ import annotations

from pathlib import Path
from typing import Dict


class UnrealPluginScaffolder:
    """Generates a complete, ready-to-build Unreal Engine 5 Live Link plugin directory."""

    @staticmethod
    def generate_plugin(output_dir: Path, plugin_name: str = "OpenLoreLiveLink") -> Dict[str, Path]:
        """Generate full plugin file tree at output_dir."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        source_dir = output_dir / "Source" / plugin_name
        public_dir = source_dir / "Public"
        private_dir = source_dir / "Private"
        scripts_dir = output_dir / "Scripts"

        public_dir.mkdir(parents=True, exist_ok=True)
        private_dir.mkdir(parents=True, exist_ok=True)
        scripts_dir.mkdir(parents=True, exist_ok=True)

        created_files: Dict[str, Path] = {}

        # 1. OpenLoreLiveLink.uplugin
        uplugin_content = f"""{{
\t"FileVersion": 3,
\t"Version": 1,
\t"VersionName": "1.0.0",
\t"FriendlyName": "OpenLore Live Link",
\t"Description": "High-speed bi-directional Live Link bridge synchronizing OpenLore USD scene replicas with Unreal Engine 5 virtual production viewports and LED volumes.",
\t"Category": "Virtual Production",
\t"CreatedBy": "OpenLore Engineering",
\t"CanContainContent": true,
\t"IsBetaVersion": false,
\t"Installed": false,
\t"Modules": [
\t\t{{
\t\t\t"Name": "{plugin_name}",
\t\t\t"Type": "Runtime",
\t\t\t"LoadingPhase": "Default",
\t\t\t"PlatformAllowList": [ "Win64", "Mac", "Linux" ]
\t\t}}
\t],
\t"Plugins": [
\t\t{{
\t\t\t"Name": "LiveLink",
\t\t\t"Enabled": true
\t\t}}
\t]
}}
"""
        uplugin_path = output_dir / f"{plugin_name}.uplugin"
        uplugin_path.write_text(uplugin_content, encoding="utf-8")
        created_files["uplugin"] = uplugin_path

        # 2. Build.cs
        build_cs_content = f"""// Copyright (c) 2026 OpenLore Project. All Rights Reserved.

using UnrealBuildTool;

public class {plugin_name} : ModuleRules
{{
\tpublic {plugin_name}(ReadOnlyTargetRules Target) : base(Target)
\t{{
\t\tPCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

\t\tPublicDependencyModuleNames.AddRange(
\t\t\tnew string[]
\t\t\t{{
\t\t\t\t"Core",
\t\t\t\t"CoreUObject",
\t\t\t\t"Engine",
\t\t\t\t"InputCore",
\t\t\t\t"LiveLinkInterface",
\t\t\t\t"LiveLinkAnimationCore",
\t\t\t\t"Networking",
\t\t\t\t"Sockets",
\t\t\t\t"Json",
\t\t\t\t"JsonUtilities"
\t\t\t}}
\t\t);
\t}}
}}
"""
        build_cs_path = source_dir / f"{plugin_name}.Build.cs"
        build_cs_path.write_text(build_cs_content, encoding="utf-8")
        created_files["build_cs"] = build_cs_path

        # 3. Module Header & Source
        mod_h = public_dir / f"{plugin_name}.h"
        mod_h.write_text(
            f"""// Copyright (c) 2026 OpenLore Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class F{plugin_name}Module : public IModuleInterface
{{
public:
\tvirtual void StartupModule() override;
\tvirtual void ShutdownModule() override;
}};
""",
            encoding="utf-8",
        )
        created_files["module_h"] = mod_h

        mod_cpp = private_dir / f"{plugin_name}.cpp"
        mod_cpp.write_text(
            f"""// Copyright (c) 2026 OpenLore Project. All Rights Reserved.

#include "{plugin_name}.h"

#define LOCTEXT_NAMESPACE "F{plugin_name}Module"

void F{plugin_name}Module::StartupModule()
{{
\tUE_LOG(LogTemp, Log, TEXT("OpenLore Live Link Module initialized"));
}}

void F{plugin_name}Module::ShutdownModule()
{{
\tUE_LOG(LogTemp, Log, TEXT("OpenLore Live Link Module shutdown"));
}}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(F{plugin_name}Module, {plugin_name})
""",
            encoding="utf-8",
        )
        created_files["module_cpp"] = mod_cpp

        # 4. OpenLoreLiveLinkSource.h
        source_h = public_dir / "OpenLoreLiveLinkSource.h"
        source_h.write_text(
            f"""// Copyright (c) 2026 OpenLore Project. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "ILiveLinkSource.h"
#include "HAL/Runnable.h"
#include "Common/UdpSocketBuilder.h"
#include "Roles/LiveLinkCameraTypes.h"
#include "Roles/LiveLinkTransformTypes.h"

class OPENLORELIVELINK_API FOpenLoreLiveLinkSource : public ILiveLinkSource, public FRunnable
{{
public:
\tFOpenLoreLiveLinkSource(const FIPv4Endpoint& InEndpoint);
\tvirtual ~FOpenLoreLiveLinkSource();

\t// ILiveLinkSource interface
\tvirtual void ReceiveClient(ILiveLinkClient* InClient, FGuid InSourceGuid) override;
\tvirtual bool IsSourceStillValid() const override;
\tvirtual bool RequestSourceShutdown() override;
\tvirtual FText GetSourceType() const override;
\tvirtual FText GetSourceMachineName() const override;
\tvirtual FText GetSourceStatus() const override;

\t// FRunnable interface
\tvirtual bool Init() override;
\tvirtual uint32 Run() override;
\tvirtual void Stop() override;
\tvirtual void Exit() override;

private:
\tvoid ParsePacket(const TArray<uint8>& Payload);

\tILiveLinkClient* Client;
\tFGuid SourceGuid;
\tFIPv4Endpoint Endpoint;
\tFSocket* Socket;
\tFRunnableThread* Thread;
\tFThreadSafeBool bIsRunning;
\tTSet<FName> RegisteredSubjects;
}};
""",
            encoding="utf-8",
        )
        created_files["source_h"] = source_h

        # 5. OpenLoreLiveLinkSource.cpp
        source_cpp = private_dir / "OpenLoreLiveLinkSource.cpp"
        source_cpp.write_text(
            f"""// Copyright (c) 2026 OpenLore Project. All Rights Reserved.

#include "OpenLoreLiveLinkSource.h"
#include "ILiveLinkClient.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Roles/LiveLinkCameraRole.h"

FOpenLoreLiveLinkSource::FOpenLoreLiveLinkSource(const FIPv4Endpoint& InEndpoint)
\t: Client(nullptr)
\t, Endpoint(InEndpoint)
\t, Socket(nullptr)
\t, Thread(nullptr)
\t, bIsRunning(false)
{{
}}

FOpenLoreLiveLinkSource::~FOpenLoreLiveLinkSource()
{{
\tStop();
\tif (Thread)
\t{{
\t\tThread->WaitForCompletion();
\t\tdelete Thread;
\t\tThread = nullptr;
\t}}
\tif (Socket)
\t{{
\t\tSocket->Close();
\t\tISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)->DestroySocket(Socket);
\t\tSocket = nullptr;
\t}}
}}

void FOpenLoreLiveLinkSource::ReceiveClient(ILiveLinkClient* InClient, FGuid InSourceGuid)
{{
\tClient = InClient;
\tSourceGuid = InSourceGuid;
\tbIsRunning = true;
\tThread = FRunnableThread::Create(this, TEXT("OpenLoreLiveLinkWorkerThread"), 128 * 1024, TPri_AboveNormal);
}}

bool FOpenLoreLiveLinkSource::IsSourceStillValid() const
{{
\treturn Client != nullptr && bIsRunning;
}}

bool FOpenLoreLiveLinkSource::RequestSourceShutdown()
{{
\tStop();
\treturn true;
}}

FText FOpenLoreLiveLinkSource::GetSourceType() const
{{
\treturn FText::FromString(TEXT("OpenLore Live Link"));
}}

FText FOpenLoreLiveLinkSource::GetSourceMachineName() const
{{
\treturn FText::FromString(Endpoint.ToString());
}}

FText FOpenLoreLiveLinkSource::GetSourceStatus() const
{{
\treturn bIsRunning ? FText::FromString(TEXT("Connected")) : FText::FromString(TEXT("Stopped"));
}}

bool FOpenLoreLiveLinkSource::Init()
{{
\tSocket = FUdpSocketBuilder(TEXT("OpenLoreLiveLinkUdpSocket"))
\t\t.AsNonBlocking()
\t\t.AsReusable()
\t\t.BoundToEndpoint(Endpoint)
\t\t.WithReceiveBufferSize(2 * 1024 * 1024);
\treturn Socket != nullptr;
}}

uint32 FOpenLoreLiveLinkSource::Run()
{{
\tTArray<uint8> Buffer;
\tBuffer.SetNumUninitialized(65535);

\twhile (bIsRunning)
\t{{
\t\tuint32 PendingDataSize = 0;
\t\tif (Socket && Socket->HasPendingData(PendingDataSize) && PendingDataSize > 0)
\t\t{{
\t\t\tint32 BytesRead = 0;
\t\t\tif (Socket->Recv(Buffer.GetData(), Buffer.Num(), BytesRead) && BytesRead > 0)
\t\t\t{{
\t\t\t\tTArray<uint8> PacketData(Buffer.GetData(), BytesRead);
\t\t\t\tParsePacket(PacketData);
\t\t\t}}
\t\t}}
\t\tFPlatformProcess::Sleep(0.001f);
\t}}
\treturn 0;
}}

void FOpenLoreLiveLinkSource::Stop()
{{
\tbIsRunning = false;
}}

void FOpenLoreLiveLinkSource::Exit()
{{
}}

void FOpenLoreLiveLinkSource::ParsePacket(const TArray<uint8>& Payload)
{{
\tif (!Client) return;

\tFString JsonStr;
\tFFileHelper::BufferToString(JsonStr, Payload.GetData(), Payload.Num());

\tTSharedPtr<FJsonObject> JsonObj;
\tTSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonStr);
\tif (!FJsonSerializer::Deserialize(Reader, JsonObj) || !JsonObj.IsValid())
\t{{
\t\treturn;
\t}}

\tFString Type = JsonObj->GetStringField(TEXT("type"));
\tFString SubjName = JsonObj->GetStringField(TEXT("subject_name"));
\tFName SubjectKey(*SubjName);
\tFLiveLinkSubjectKey Key(SourceGuid, SubjectKey);

\tif (Type == TEXT("StaticData"))
\t{{
\t\tFLiveLinkStaticDataStruct StaticData(FLiveLinkCameraStaticData::StaticStruct());
\t\tFLiveLinkCameraStaticData& CamStatic = *StaticData.Cast<FLiveLinkCameraStaticData>();
\t\tCamStatic.bIsFocalLengthSupported = true;
\t\tCamStatic.bIsApertureSupported = true;
\t\tCamStatic.bIsFocusDistanceSupported = true;
\t\tCamStatic.bIsFieldOfViewSupported = true;

\t\tif (!RegisteredSubjects.Contains(SubjectKey))
\t\t{{
\t\t\tClient->PushSubjectStaticData_AnyThread(Key, ULiveLinkCameraRole::StaticClass(), MoveTemp(StaticData));
\t\t\tRegisteredSubjects.Add(SubjectKey);
\t\t}}
\t}}
\telse if (Type == TEXT("FrameData"))
\t{{
\t\tFLiveLinkFrameDataStruct FrameData(FLiveLinkCameraFrameData::StaticStruct());
\t\tFLiveLinkCameraFrameData& CamFrame = *FrameData.Cast<FLiveLinkCameraFrameData>();

\t\tconst TSharedPtr<FJsonObject>* TfObj;
\t\tif (JsonObj->TryGetObjectField(TEXT("transform"), TfObj))
\t\t{{
\t\t\tconst TArray<TSharedPtr<FJsonValue>>* TransArr;
\t\t\tif ((*TfObj)->TryGetArrayField(TEXT("translation"), TransArr) && TransArr->Num() >= 3)
\t\t\t{{
\t\t\t\tCamFrame.Transform.SetLocation(FVector(
\t\t\t\t\t(*TransArr)[0]->AsNumber(),
\t\t\t\t\t(*TransArr)[1]->AsNumber(),
\t\t\t\t\t(*TransArr)[2]->AsNumber()
\t\t\t\t));
\t\t\t}}
\t\t\tconst TArray<TSharedPtr<FJsonValue>>* RotArr;
\t\t\tif ((*TfObj)->TryGetArrayField(TEXT("rotation"), RotArr) && RotArr->Num() >= 4)
\t\t\t{{
\t\t\t\tCamFrame.Transform.SetRotation(FQuat(
\t\t\t\t\t(*RotArr)[0]->AsNumber(),
\t\t\t\t\t(*RotArr)[1]->AsNumber(),
\t\t\t\t\t(*RotArr)[2]->AsNumber(),
\t\t\t\t\t(*RotArr)[3]->AsNumber()
\t\t\t\t));
\t\t\t}}
\t\t}}

\t\tconst TSharedPtr<FJsonObject>* CamObj;
\t\tif (JsonObj->TryGetObjectField(TEXT("camera_frame_data"), CamObj))
\t\t{{
\t\t\tCamFrame.FieldOfView = (*CamObj)->GetNumberField(TEXT("field_of_view"));
\t\t\tCamFrame.FocalLength = (*CamObj)->GetNumberField(TEXT("focal_length"));
\t\t\tCamFrame.Aperture = (*CamObj)->GetNumberField(TEXT("aperture"));
\t\t\tCamFrame.FocusDistance = (*CamObj)->GetNumberField(TEXT("focus_distance"));
\t\t}}

\t\tClient->PushSubjectFrameData_AnyThread(Key, MoveTemp(FrameData));
\t}}
}}
""",
            encoding="utf-8",
        )
        created_files["source_cpp"] = source_cpp

        # 6. Python Editor Script
        py_script = scripts_dir / "openlore_livelink_editor.py"
        py_script.write_text(
            """# OpenLore Live Link Unreal Editor Automation Script
import unreal
import socket
import json

def listen_to_openlore(port=11111):
    \"\"\"Run within Unreal Editor Output Log / Python tab to test OpenLore UDP packets.\"\"\"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))
    sock.settimeout(2.0)
    unreal.log(f"[OpenLore] Listening on 127.0.0.1:{port}...")
    try:
        data, _ = sock.recvfrom(65535)
        parsed = json.loads(data.decode("utf-8"))
        unreal.log(f"[OpenLore] Received packet: {parsed.get('subject_name')} ({parsed.get('type')})")
        return parsed
    except socket.timeout:
        unreal.log_warning("[OpenLore] No packets received before timeout.")
    finally:
        sock.close()
""",
            encoding="utf-8",
        )
        created_files["py_script"] = py_script

        # 7. Documentation
        readme = output_dir / "README.md"
        readme.write_text(
            f"""# {plugin_name} (Unreal Engine 5 Live Link Plugin)

Turnkey Unreal Engine 5 Live Link integration for **OpenLore** (*"Git for 3D worlds, game lore, and Hollywood pipelines"*).

## Installation

1. Copy the `{plugin_name}` directory into your Unreal Engine project's `Plugins/` folder:
   ```bash
   cp -r {plugin_name} <MyProject>/Plugins/
   ```
2. Enable the plugin in Unreal Engine: **Edit > Plugins > Virtual Production > OpenLore Live Link**.
3. In the Live Link window (**Window > Virtual Production > Live Link**), add source: **OpenLore Live Link Source** (`127.0.0.1:11111`).
4. Camera and transform subjects will appear automatically under Subject Name (e.g. `Camera_StageA`).
""",
            encoding="utf-8",
        )
        created_files["readme"] = readme

        return created_files

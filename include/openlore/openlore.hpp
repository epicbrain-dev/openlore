/**
 * OpenLore C++ Native DCC SDK
 * 
 * High-performance, zero-dependency, header-only C++17 library for virtual production,
 * low-latency DCC Live Link streaming, causal vector clocks, and cryptographic CAS asset bindings.
 * 
 * Supported Platforms: Linux, macOS, Windows
 * Compatible DCCs: Unreal Engine 5, SideFX Houdini HDK, Autodesk Maya C++, Blender C/C++, Custom Engines
 * 
 * Copyright (c) 2026 OpenLore Engineering. All rights reserved.
 * Licensed under the Apache License, Version 2.0.
 */

#pragma once

#ifndef OPENLORE_HPP
#define OPENLORE_HPP

#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <unordered_map>
#include <chrono>
#include <cmath>
#include <stdexcept>
#include <algorithm>
#include <array>

#if defined(_WIN32) || defined(_WIN64)
    #define OPENLORE_PLATFORM_WINDOWS
    #ifndef WIN32_LEAN_AND_MEAN
        #define WIN32_LEAN_AND_MEAN
    #endif
    #include <windows.h>
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
#else
    #define OPENLORE_PLATFORM_POSIX
    #include <sys/types.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <fcntl.h>
#endif

namespace OpenLore {

constexpr const char* VERSION = "1.5.0";
constexpr uint32_t MAGIC_HEADER = 0x4F4C4C4B; // 'OLLK' in big-endian
constexpr uint8_t PROTOCOL_VERSION = 1;

enum class SubjectType : uint8_t {
    Transform = 0,
    Camera = 1,
    Animation = 2
};

struct Vector3 {
    float x{0.0f}, y{0.0f}, z{0.0f};

    Vector3() = default;
    Vector3(float inX, float inY, float inZ) : x(inX), y(inY), z(inZ) {}
};

struct Quaternion {
    float x{0.0f}, y{0.0f}, z{0.0f}, w{1.0f};

    Quaternion() = default;
    Quaternion(float inX, float inY, float inZ, float inW) : x(inX), y(inY), z(inZ), w(inW) {}
};

struct CameraParams {
    float field_of_view{39.6f};   // degrees
    float focal_length{50.0f};    // mm
    float aperture{2.8f};         // f-stop
    float focus_distance{1000.0f};// cm
};

struct CoordinateConverter {
    // OpenUSD (Right-Handed Z-Up) to Unreal Engine 5 (Left-Handed Z-Up, cm)
    static Vector3 UsdToUnrealPosition(const Vector3& posUsd, float metersPerUnit = 1.0f) {
        float scale = metersPerUnit * 100.0f;
        return Vector3(posUsd.x * scale, -posUsd.y * scale, posUsd.z * scale);
    }

    // Unreal Engine 5 (cm) to OpenUSD (meters)
    static Vector3 UnrealToUsdPosition(const Vector3& posUe, float metersPerUnit = 1.0f) {
        float scale = 1.0f / (metersPerUnit * 100.0f);
        return Vector3(posUe.x * scale, -posUe.y * scale, posUe.z * scale);
    }

    // Chirality conversion for quaternions
    static Quaternion UsdToUnrealQuaternion(const Quaternion& q) {
        return Quaternion(q.x, -q.y, q.z, -q.w);
    }

    static Quaternion UnrealToUsdQuaternion(const Quaternion& q) {
        return Quaternion(q.x, -q.y, q.z, -q.w);
    }
};

// Endian conversion helpers
inline uint16_t SwapBE16(uint16_t val) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_bswap16(val);
#else
    return (val << 8) | (val >> 8);
#endif
}

inline uint32_t SwapBE32(uint32_t val) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_bswap32(val);
#else
    return ((val >> 24) & 0xff) | ((val << 8) & 0xff0000) | ((val >> 8) & 0xff00) | ((val << 24) & 0xff000000);
#endif
}

inline uint64_t SwapBE64(uint64_t val) {
#if defined(__GNUC__) || defined(__clang__)
    return __builtin_bswap64(val);
#else
    return ((val >> 56) & 0x00000000000000FFULL) |
           ((val >> 40) & 0x000000000000FF00ULL) |
           ((val >> 24) & 0x0000000000FF0000ULL) |
           ((val >> 8)  & 0x00000000FF000000ULL) |
           ((val << 8)  & 0x000000FF00000000ULL) |
           ((val << 24) & 0x0000FF0000000000ULL) |
           ((val << 40) & 0x00FF000000000000ULL) |
           ((val << 56) & 0xFF00000000000000ULL);
#endif
}

inline float SwapBEFloat(float val) {
    uint32_t temp;
    std::memcpy(&temp, &val, sizeof(float));
    temp = SwapBE32(temp);
    float res;
    std::memcpy(&res, &temp, sizeof(float));
    return res;
}

inline double SwapBEDouble(double val) {
    uint64_t temp;
    std::memcpy(&temp, &val, sizeof(double));
    temp = SwapBE64(temp);
    double res;
    std::memcpy(&res, &temp, sizeof(double));
    return res;
}

struct LiveLinkFrame {
    std::string subject_name{"Camera_Hero"};
    SubjectType subject_type{SubjectType::Camera};
    double timestamp{0.0};
    uint32_t frame_number{0};
    Vector3 translation{0.0f, 0.0f, 0.0f};
    Quaternion rotation{0.0f, 0.0f, 0.0f, 1.0f};
    Vector3 scale{1.0f, 1.0f, 1.0f};
    CameraParams camera;

    std::vector<uint8_t> SerializeBinary() const {
        std::vector<uint8_t> buf;
        // Header: 4 bytes Magic, 1 byte Version, 1 byte Role, 2 bytes NameLen
        buf.push_back('O');
        buf.push_back('L');
        buf.push_back('L');
        buf.push_back('K');
        buf.push_back(PROTOCOL_VERSION);
        buf.push_back(static_cast<uint8_t>(subject_type));

        uint16_t nameLen = SwapBE16(static_cast<uint16_t>(subject_name.size()));
        const uint8_t* nameLenPtr = reinterpret_cast<const uint8_t*>(&nameLen);
        buf.insert(buf.end(), nameLenPtr, nameLenPtr + 2);

        // Subject Name
        buf.insert(buf.end(), subject_name.begin(), subject_name.end());

        // Body:
        // double timestamp (8), uint32 frame_number (4)
        double beTimestamp = SwapBEDouble(timestamp);
        const uint8_t* tsPtr = reinterpret_cast<const uint8_t*>(&beTimestamp);
        buf.insert(buf.end(), tsPtr, tsPtr + 8);

        uint32_t beFrameNum = SwapBE32(frame_number);
        const uint8_t* fnPtr = reinterpret_cast<const uint8_t*>(&beFrameNum);
        buf.insert(buf.end(), fnPtr, fnPtr + 4);

        // Translation 3f
        float tX = SwapBEFloat(translation.x);
        float tY = SwapBEFloat(translation.y);
        float tZ = SwapBEFloat(translation.z);
        const uint8_t* txPtr = reinterpret_cast<const uint8_t*>(&tX);
        const uint8_t* tyPtr = reinterpret_cast<const uint8_t*>(&tY);
        const uint8_t* tzPtr = reinterpret_cast<const uint8_t*>(&tZ);
        buf.insert(buf.end(), txPtr, txPtr + 4);
        buf.insert(buf.end(), tyPtr, tyPtr + 4);
        buf.insert(buf.end(), tzPtr, tzPtr + 4);

        // Rotation 4f
        float rX = SwapBEFloat(rotation.x);
        float rY = SwapBEFloat(rotation.y);
        float rZ = SwapBEFloat(rotation.z);
        float rW = SwapBEFloat(rotation.w);
        const uint8_t* rxPtr = reinterpret_cast<const uint8_t*>(&rX);
        const uint8_t* ryPtr = reinterpret_cast<const uint8_t*>(&rY);
        const uint8_t* rzPtr = reinterpret_cast<const uint8_t*>(&rZ);
        const uint8_t* rwPtr = reinterpret_cast<const uint8_t*>(&rW);
        buf.insert(buf.end(), rxPtr, rxPtr + 4);
        buf.insert(buf.end(), ryPtr, ryPtr + 4);
        buf.insert(buf.end(), rzPtr, rzPtr + 4);
        buf.insert(buf.end(), rwPtr, rwPtr + 4);

        // Scale 3f
        float sX = SwapBEFloat(scale.x);
        float sY = SwapBEFloat(scale.y);
        float sZ = SwapBEFloat(scale.z);
        buf.insert(buf.end(), reinterpret_cast<const uint8_t*>(&sX), reinterpret_cast<const uint8_t*>(&sX) + 4);
        buf.insert(buf.end(), reinterpret_cast<const uint8_t*>(&sY), reinterpret_cast<const uint8_t*>(&sY) + 4);
        buf.insert(buf.end(), reinterpret_cast<const uint8_t*>(&sZ), reinterpret_cast<const uint8_t*>(&sZ) + 4);

        // Camera params 4f
        float cFov = SwapBEFloat(camera.field_of_view);
        float cFocal = SwapBEFloat(camera.focal_length);
        float cAp = SwapBEFloat(camera.aperture);
        float cFocDist = SwapBEFloat(camera.focus_distance);
        buf.insert(buf.end(), reinterpret_cast<const uint8_t*>(&cFov), reinterpret_cast<const uint8_t*>(&cFov) + 4);
        buf.insert(buf.end(), reinterpret_cast<const uint8_t*>(&cFocal), reinterpret_cast<const uint8_t*>(&cFocal) + 4);
        buf.insert(buf.end(), reinterpret_cast<const uint8_t*>(&cAp), reinterpret_cast<const uint8_t*>(&cAp) + 4);
        buf.insert(buf.end(), reinterpret_cast<const uint8_t*>(&cFocDist), reinterpret_cast<const uint8_t*>(&cFocDist) + 4);

        return buf;
    }

    static LiveLinkFrame DeserializeBinary(const uint8_t* data, size_t size) {
        if (size < 8) {
            throw std::runtime_error("Payload too short for LiveLink header");
        }
        if (std::memcmp(data, "OLLK", 4) != 0) {
            throw std::runtime_error("Invalid magic binary header");
        }
        uint8_t version = data[4];
        if (version != PROTOCOL_VERSION) {
            throw std::runtime_error("Unsupported LiveLink protocol version");
        }
        uint8_t roleId = data[5];
        uint16_t nameLenBe;
        std::memcpy(&nameLenBe, data + 6, 2);
        uint16_t nameLen = SwapBE16(nameLenBe);

        if (size < 8 + nameLen + 64) {
            throw std::runtime_error("Payload truncated");
        }

        LiveLinkFrame frame;
        frame.subject_name = std::string(reinterpret_cast<const char*>(data + 8), nameLen);
        frame.subject_type = static_cast<SubjectType>(roleId);

        const uint8_t* body = data + 8 + nameLen;

        double beTs;
        std::memcpy(&beTs, body, 8);
        frame.timestamp = SwapBEDouble(beTs);

        uint32_t beFn;
        std::memcpy(&beFn, body + 8, 4);
        frame.frame_number = SwapBE32(beFn);

        float t[3];
        std::memcpy(t, body + 12, 12);
        frame.translation = Vector3(SwapBEFloat(t[0]), SwapBEFloat(t[1]), SwapBEFloat(t[2]));

        float r[4];
        std::memcpy(r, body + 24, 16);
        frame.rotation = Quaternion(SwapBEFloat(r[0]), SwapBEFloat(r[1]), SwapBEFloat(r[2]), SwapBEFloat(r[3]));

        float s[3];
        std::memcpy(s, body + 40, 12);
        frame.scale = Vector3(SwapBEFloat(s[0]), SwapBEFloat(s[1]), SwapBEFloat(s[2]));

        float c[4];
        std::memcpy(c, body + 52, 16);
        frame.camera.field_of_view = SwapBEFloat(c[0]);
        frame.camera.focal_length = SwapBEFloat(c[1]);
        frame.camera.aperture = SwapBEFloat(c[2]);
        frame.camera.focus_distance = SwapBEFloat(c[3]);

        return frame;
    }
};

// Causal Ordering Engine
class VectorClock {
public:
    std::unordered_map<std::string, uint64_t> clock;

    VectorClock() = default;

    void Increment(const std::string& studioId) {
        clock[studioId]++;
    }

    uint64_t Get(const std::string& studioId) const {
        auto it = clock.find(studioId);
        return (it != clock.end()) ? it->second : 0ULL;
    }

    bool Dominates(const VectorClock& other) const {
        bool strictlyGreater = false;
        for (const auto& [k, v] : other.clock) {
            if (Get(k) < v) return false;
            if (Get(k) > v) strictlyGreater = true;
        }
        for (const auto& [k, v] : clock) {
            if (other.Get(k) < v) strictlyGreater = true;
        }
        return strictlyGreater;
    }

    void Merge(const VectorClock& other) {
        for (const auto& [k, v] : other.clock) {
            clock[k] = std::max(clock[k], v);
        }
    }
};

// Content-Addressed Storage BLAKE3 Hash Representation
class CASHash {
public:
    std::string hex;

    CASHash() : hex(64, '0') {}
    explicit CASHash(const std::string& inHex) {
        if (!IsValid(inHex)) {
            throw std::invalid_argument("Invalid CAS BLAKE3 hash: must be 64-char hexadecimal");
        }
        hex = inHex;
        std::transform(hex.begin(), hex.end(), hex.begin(), ::tolower);
    }

    static bool IsValid(const std::string& str) {
        if (str.size() != 64) return false;
        for (char c : str) {
            if (!std::isxdigit(static_cast<unsigned char>(c))) return false;
        }
        return true;
    }

    std::string ShardPath() const {
        return "objects/" + hex.substr(0, 2) + "/" + hex.substr(2, 2) + "/" + hex;
    }
};

// Zero-dependency UDP Broadcast Client for DCC Viewports
class UDPBroadcastClient {
private:
    int sock_{-1};
    struct sockaddr_in target_addr_{};
    bool is_open_{false};

public:
    UDPBroadcastClient() = default;
    ~UDPBroadcastClient() { Close(); }

    bool Open(const std::string& host = "127.0.0.1", int port = 11111) {
        Close();
#if defined(OPENLORE_PLATFORM_WINDOWS)
        WSADATA wsaData;
        WSAStartup(MAKEWORD(2, 2), &wsaData);
#endif
        sock_ = socket(AF_INET, SOCK_DGRAM, 0);
        if (sock_ < 0) return false;

        std::memset(&target_addr_, 0, sizeof(target_addr_));
        target_addr_.sin_family = AF_INET;
        target_addr_.sin_port = htons(static_cast<uint16_t>(port));
        inet_pton(AF_INET, host.c_str(), &target_addr_.sin_addr);

        is_open_ = true;
        return true;
    }

    bool SendFrame(const LiveLinkFrame& frame) {
        if (!is_open_ || sock_ < 0) return false;
        std::vector<uint8_t> payload = frame.SerializeBinary();
        ssize_t sent = sendto(
            sock_,
            reinterpret_cast<const char*>(payload.data()),
            payload.size(),
            0,
            reinterpret_cast<struct sockaddr*>(&target_addr_),
            sizeof(target_addr_)
        );
        return sent == static_cast<ssize_t>(payload.size());
    }

    void Close() {
        if (is_open_ && sock_ >= 0) {
#if defined(OPENLORE_PLATFORM_WINDOWS)
            closesocket(sock_);
            WSACleanup();
#else
            close(sock_);
#endif
            sock_ = -1;
            is_open_ = false;
        }
    }
};

} // namespace OpenLore

#endif // OPENLORE_HPP

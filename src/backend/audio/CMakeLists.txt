cmake_minimum_required(VERSION 3.28)

project(audio LANGUAGES C CXX)

include(FetchContent)

FetchContent_Declare(
    juce
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG 19edd538429c93d277bf95b55aaa7e3eb545f951)

FetchContent_Declare(
    tracktion_engine
    GIT_REPOSITORY https://github.com/Tracktion/tracktion_engine.git
    GIT_TAG v3.2.0
    GIT_SUBMODULES ""
    GIT_SHALLOW ON
    SOURCE_SUBDIR modules)

FetchContent_Declare(
    protobuf
    URL https://github.com/protocolbuffers/protobuf/releases/download/v36.1/protobuf-36.1.tar.gz
    URL_HASH SHA256=dc74fa582f559cbd31614ddfefb4868f43c919d7184bde514bb47f90c6025eb8
    EXCLUDE_FROM_ALL)

set(protobuf_INSTALL OFF CACHE BOOL "" FORCE)
set(protobuf_MSVC_STATIC_RUNTIME OFF CACHE BOOL "" FORCE)
set(protobuf_BUILD_PROTOC_BINARIES OFF CACHE BOOL "" FORCE)
set(protobuf_BUILD_LIBPROTOC OFF CACHE BOOL "" FORCE)
set(protobuf_BUILD_LIBUPB OFF CACHE BOOL "" FORCE)

if (APPLE)
    set(proof_schema_protoc_url https://github.com/protocolbuffers/protobuf/releases/download/v36.1/protoc-36.1-osx-aarch_64.zip)
    set(proof_schema_protoc_hash SHA256=de56d57afe30c5d191b11d24ff93dd4025728d7fb43b773886b2d3613e0bdbb2)
elseif (WIN32)
    set(proof_schema_protoc_url https://github.com/protocolbuffers/protobuf/releases/download/v36.1/protoc-36.1-win64.zip)
    set(proof_schema_protoc_hash SHA256=390e515cb456e6a978553bdb57baf087b054885077fd6da7f7ff0160279c07d6)
else ()
    message(FATAL_ERROR "No prebuilt protoc binary declared for this platform in src/backend/audio/CMakeLists.txt")
endif ()

FetchContent_Declare(
    protoc_binary
    URL ${proof_schema_protoc_url}
    URL_HASH ${proof_schema_protoc_hash})

FetchContent_MakeAvailable(juce)
FetchContent_MakeAvailable(tracktion_engine)
FetchContent_MakeAvailable(protobuf)
FetchContent_MakeAvailable(protoc_binary)

if (WIN32)
    set(proof_schema_protoc_exe ${protoc_binary_SOURCE_DIR}/bin/protoc.exe)
else ()
    set(proof_schema_protoc_exe ${protoc_binary_SOURCE_DIR}/bin/protoc)
endif ()

set(proof_schema_dir ${CMAKE_CURRENT_SOURCE_DIR}/../../schemas)
set(proof_schema_generated_dir ${CMAKE_CURRENT_BINARY_DIR}/generated)
file(MAKE_DIRECTORY ${proof_schema_generated_dir})

add_custom_command(
    OUTPUT ${proof_schema_generated_dir}/proof.pb.cc ${proof_schema_generated_dir}/proof.pb.h
    COMMAND ${proof_schema_protoc_exe}
    ARGS --cpp_out=${proof_schema_generated_dir} -I ${proof_schema_dir} ${proof_schema_dir}/proof.proto
    DEPENDS ${proof_schema_protoc_exe} ${proof_schema_dir}/proof.proto)

add_library(proof_proto STATIC ${proof_schema_generated_dir}/proof.pb.cc)

target_include_directories(proof_proto PUBLIC ${proof_schema_generated_dir})

target_compile_features(proof_proto PUBLIC cxx_std_17)

target_link_libraries(proof_proto PUBLIC protobuf::libprotobuf)

add_executable(proof_schema tests/proof_schema.cpp)

target_link_libraries(proof_schema PRIVATE proof_proto)

add_custom_command(
    OUTPUT ${proof_schema_generated_dir}/project.pb.cc ${proof_schema_generated_dir}/project.pb.h
    COMMAND ${proof_schema_protoc_exe}
    ARGS --cpp_out=${proof_schema_generated_dir} -I ${proof_schema_dir} ${proof_schema_dir}/project.proto
    DEPENDS ${proof_schema_protoc_exe} ${proof_schema_dir}/project.proto)

add_library(project_proto STATIC ${proof_schema_generated_dir}/project.pb.cc)

target_include_directories(project_proto PUBLIC ${proof_schema_generated_dir})

target_compile_features(project_proto PUBLIC cxx_std_17)

target_link_libraries(project_proto PUBLIC protobuf::libprotobuf)

add_executable(project_schema tests/project_schema.cpp)

target_link_libraries(project_schema PRIVATE project_proto)

add_executable(transport_proof tests/transport_proof.cpp)

target_link_libraries(transport_proof PRIVATE proof_proto juce::juce_events)

add_executable(toolchain_proof tests/toolchain_proof.cpp)

target_compile_features(toolchain_proof PRIVATE cxx_std_20)

target_compile_definitions(toolchain_proof PRIVATE
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0
    JUCE_MODAL_LOOPS_PERMITTED=1)

target_link_libraries(toolchain_proof PRIVATE
    tracktion::tracktion_core
    tracktion::tracktion_engine
    tracktion::tracktion_graph
    juce::juce_audio_devices
    juce::juce_audio_utils)

add_library(materializer STATIC materializer.cpp)

target_include_directories(materializer PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

target_compile_features(materializer PUBLIC cxx_std_20)

target_compile_definitions(materializer PRIVATE
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0
    JUCE_MODAL_LOOPS_PERMITTED=1)

target_link_libraries(materializer PUBLIC
    tracktion::tracktion_core
    tracktion::tracktion_engine
    tracktion::tracktion_graph
    juce::juce_audio_formats
    juce::juce_audio_devices)

add_executable(materializer_proof tests/materializer_proof.cpp)

target_compile_definitions(materializer_proof PRIVATE
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0
    JUCE_MODAL_LOOPS_PERMITTED=1)

target_link_libraries(materializer_proof PRIVATE
    materializer
    juce::juce_audio_devices
    juce::juce_audio_utils)

add_executable(live_session_proof tests/live_session_proof.cpp)

target_compile_definitions(live_session_proof PRIVATE
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0
    JUCE_MODAL_LOOPS_PERMITTED=1)

target_link_libraries(live_session_proof PRIVATE
    materializer
    juce::juce_audio_devices
    juce::juce_audio_utils)

add_executable(playback_proof tests/playback_proof.cpp)

target_compile_definitions(playback_proof PRIVATE
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0
    JUCE_MODAL_LOOPS_PERMITTED=1)

target_link_libraries(playback_proof PRIVATE
    materializer
    juce::juce_audio_devices
    juce::juce_audio_utils)

add_library(wire_codec STATIC wire_codec.cpp)

target_compile_features(wire_codec PRIVATE cxx_std_17)

target_link_libraries(wire_codec PRIVATE project_proto)

add_executable(native_runtime native_runtime.cpp)

target_compile_definitions(native_runtime PRIVATE
    JUCE_USE_CURL=0
    JUCE_WEB_BROWSER=0
    JUCE_MODAL_LOOPS_PERMITTED=1)

target_link_libraries(native_runtime PRIVATE
    materializer
    wire_codec
    juce::juce_audio_devices
    juce::juce_audio_utils
    juce::juce_events)

enable_testing()
add_test(NAME toolchain_proof COMMAND toolchain_proof)
add_test(NAME proof_schema COMMAND proof_schema)
add_test(NAME project_schema COMMAND project_schema)
add_test(NAME materializer_proof COMMAND materializer_proof)
add_test(NAME live_session_proof COMMAND live_session_proof)
add_test(NAME playback_proof COMMAND playback_proof)

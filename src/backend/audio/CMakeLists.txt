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

add_executable(proof_schema proof_schema.cpp ${proof_schema_generated_dir}/proof.pb.cc)

target_include_directories(proof_schema PRIVATE ${proof_schema_generated_dir})

target_compile_features(proof_schema PRIVATE cxx_std_17)

target_link_libraries(proof_schema PRIVATE protobuf::libprotobuf)

add_executable(toolchain_proof toolchain_proof.cpp)

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

enable_testing()
add_test(NAME toolchain_proof COMMAND toolchain_proof)
add_test(NAME proof_schema COMMAND proof_schema)

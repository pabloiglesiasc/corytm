cmake_minimum_required(VERSION 3.22)

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

FetchContent_MakeAvailable(juce)
FetchContent_MakeAvailable(tracktion_engine)

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

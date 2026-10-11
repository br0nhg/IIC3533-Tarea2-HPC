# Compila las versiones C++ con -O3 -march=native -fopenmp (o equivalente).
# macOS (Apple clang): OpenMP via libomp de Homebrew; en ARM se usa -mcpu=native.
# Linux (g++): flags estandar.

UNAME := $(shell uname -s)
BIN   := bin

ifeq ($(UNAME),Darwin)
  CXX      ?= clang++
  LIBOMP   := $(shell brew --prefix libomp 2>/dev/null)
  ARCHFLAG := $(if $(filter arm64,$(shell uname -m)),-mcpu=native,-march=native)
  CXXFLAGS := -O3 $(ARCHFLAG) -std=c++17 -Xpreprocessor -fopenmp -I$(LIBOMP)/include
  LDFLAGS  := -L$(LIBOMP)/lib -lomp
else
  CXX      := g++
  CXXFLAGS := -O3 -march=native -std=c++17 -fopenmp
  LDFLAGS  :=
endif

TARGETS := $(BIN)/serial $(BIN)/alg1_omp $(BIN)/alg2_dc_omp

all: $(TARGETS)

$(BIN):
	mkdir -p $(BIN)

$(BIN)/serial: serial.cpp | $(BIN)
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

$(BIN)/%: src/%.cpp src/common.hpp | $(BIN)
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDFLAGS)

clean:
	rm -rf $(BIN)

.PHONY: all clean

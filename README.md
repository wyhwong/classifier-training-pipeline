# TAO-like PyTorch Object Classifier Training Pipeline
This repository aims to provide a primitive tool to finetune state-of-the-art models with PyTorch implementation, similar to Nvidia TAO but with more flexibility in augmentation and models. Like TAO classification, all parameters are configurable in [setting.yml](./pipeline/setting.yml) to minimize the need of modifying scripts.

Get config ready, get dataset ready, no coding (hopefully :D), start PyTorch training.

## Prerequisites
- Docker: [https://www.docker.com/](https://www.docker.com/)
- Poetry: [https://python-poetry.org](https://python-poetry.org)
- GNU make: [https://www.gnu.org/software/make/manual/make.html](https://www.gnu.org/software/make/manual/make.html)

## Main Features
- [x] Easy-to-use commands with GNU Make
- [x] Docker containerized environment
- [x] Poetry dependency management

## Usage
Please see [README.md](./pipeline/README.md) inside `pipeline` folder.

## Features To Be Developed
1. Implement detector training

## Author
[@wyhwong](https://github.com/wyhwong)

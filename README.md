# DL-FL-Workshop
This repository contains all examples discussed in the [NHR4CES](https://www.nhr4ces.de/) workshop on Distributed and Federated Learning.

## Abstract
Today more data is gathered than ever before. This does not only hold for economic data, but also for research-data. At the same time, the need for ML-methods is higher than ever in research and other domains. Often the datasets used in ML-tasks are too big to be processed by a single work-station or even a single server. Distributed- and Federated Learning help to handle large datasets in a distributed way, even with privacy-guarantees in the case of Federated Learning.

## Distributed Learning
We provide examples for data parallel training, pipeline parallel training and a mix of data parallel and pipeline parallel training. All examples are implemented in pytorch and aim to demonstrate distributed learning of a GPT-2 model. The examples are mostly based on [pytorch examples](https://github.com/pytorch/examples) repository. 

## Federated Learning
To demonstrate federated learning, we aim to learn a CNN classifying CIFAR-10 images. We base our example on an example shown by [flower](https://github.com/adap/flower).
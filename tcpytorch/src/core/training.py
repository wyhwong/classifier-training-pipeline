from copy import deepcopy
from datetime import datetime
from typing import Optional

import numpy as np
import torch
import torchvision
from tqdm import tqdm

import env
import core.utils
import schemas.constants
import logger


local_logger = logger.get_logger(__name__)


def train_model(
    model: torchvision.models,
    dataloaders: dict[str, torchvision.datasets.ImageFolder],
    criterion: torch.nn.Module,
    optimizer: torch.optim,
    scheduler: torch.optim.lr_scheduler,
    num_epochs: int,
    best_criteria: schemas.constants.BestCriteria,
) -> tuple:
    """
    Train the model.

    Args:
    -----
        model: torchvision.models
            Model to train.

        dataloaders: dict[str, torchvision.datasets.ImageFolder]
            Dataloaders for training and validation.

        criterion: torch.nn.Module
            Criterion for the model.

        optimizer: torch.optim
            Optimizer for the model.

        scheduler: torch.optim.lr_scheduler
            Scheduler for the optimizer.

        num_epochs: int
            Number of epochs to train.

        best_criteria: schemas.constants.BestCriteria
            Best criteria to save the best model.

    Returns:
    --------
        model: torchvision.models
            Trained model.

        best_weights: dict
            Best weights of the model.

        last_weights: dict
            Last weights of the model.

        train_loss: dict[str, list]
            Training loss of the model.

        train_acc: dict[str, list]
            Training accuracy of the model.
    """

    training_start = datetime.now()
    local_logger.info("Start time of training: %s", training_start)
    local_logger.info("Training using device: %s", env.DEVICE)

    best_weights = deepcopy(model.state_dict())
    train_loss: dict[str, list] = {"train": [], "val": []}
    train_acc: dict[str, list] = {"train": [], "val": []}
    best_record = np.inf if best_criteria is schemas.constants.BestCriteria.LOSS else -np.inf

    for epoch in range(1, num_epochs + 1):
        local_logger.info("-" * 40)
        local_logger.info("Epoch %d/%d", epoch, num_epochs)
        local_logger.info("-" * 20)

        for phase in [schemas.constants.Phase.TRAINING, schemas.constants.Phase.VALIDATION]:
            if phase is schemas.constants.Phase.TRAINING:
                local_logger.debug("The %d-th epoch training started.", epoch)
                model.train()
            else:
                local_logger.debug("The %d-th epoch validation started.", epoch)
                model.eval()

            epoch_loss = np.inf
            epoch_corrects = 0
            for inputs, labels in tqdm(dataloaders[phase.value]):
                inputs = inputs.to(env.DEVICE)
                labels = labels.to(env.DEVICE)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase is schemas.constants.Phase.TRAINING):
                    outputs = model(inputs.float())
                    loss = criterion(outputs, labels)
                    _, preds = torch.max(outputs, 1)

                    if phase is schemas.constants.Phase.TRAINING:
                        loss.backward()
                        optimizer.step()

                epoch_loss += loss.item() * inputs.size(0)
                epoch_corrects += torch.sum(preds == labels.data).double()

            epoch_loss = epoch_loss / len(dataloaders[phase.value].dataset)
            epoch_acc = epoch_corrects / len(dataloaders[phase.value].dataset)

            if scheduler and phase is schemas.constants.Phase.TRAINING:
                scheduler.step()
                local_logger.info("Last learning rate in this epoch: %.3f", scheduler.get_last_lr()[0])

            local_logger.info("%s Loss: %.4f Acc: %.4f.", phase, epoch_loss, epoch_acc)

            if phase is schemas.constants.Phase.VALIDATION:
                if best_criteria is schemas.constants.BestCriteria.LOSS and epoch_loss < best_record:
                    local_logger.info("New Record: %.4f < %.4f", epoch_loss, best_record)
                    best_record = epoch_loss
                    best_weights = deepcopy(model.state_dict())
                    local_logger.debug("Updated best models.")

                if best_criteria is schemas.constants.BestCriteria.ACCURACY and epoch_acc > best_record:
                    local_logger.info("New Record: %.4f < %.4f", epoch_acc, best_record)
                    best_record = epoch_acc
                    best_weights = deepcopy(model.state_dict())
                    local_logger.debug("Updated best models.")

            train_acc[phase.value].append(float(epoch_acc))
            train_loss[phase.value].append(float(epoch_loss))
            local_logger.debug("Updated train_acc, train_loss: %.4f, %.4f", epoch_acc, epoch_loss)

    last_weights = deepcopy(model.state_dict())
    time_elapsed = (datetime.now() - training_start).total_seconds()
    local_logger.info("Training complete at %s", datetime.now())
    local_logger.info("Training complete in %dm %ds.", time_elapsed // 60, time_elapsed % 60)
    local_logger.info("Best val %s: %.4f}.", best_criteria, best_record)
    return model, best_weights, last_weights, train_loss, train_acc


def get_optimizer(
    params: torch.nn.Module.parameters,
    optimizier=schemas.constants.OptimizerType,
    lr=1e-3,
    momentum=0.9,
    weight_decay=0.0,
    alpha=0.99,
    betas=(0.9, 0.999),
) -> torch.optim:
    """
    Get optimizer for the model.

    Args:
    -----
        params: torch.nn.Module.parameters
            Parameters of the model.

        optimizier: schemas.constants.OptimizerType
            Optimizer type.

        lr: float, optional
            Learning rate for the optimizer.

        momentum: float, optional
            Momentum for the optimizer.

        weight_decay: float, optional
            Weight decay for the optimizer.

        alpha: float, optional
            Alpha for the optimizer.

        betas: tuple, optional
            Betas for the optimizer.

    Returns:
    --------
        optimizer: torch.optim
            Optimizer for the model.
    """

    local_logger.info("Creating optimizer: %s", optimizier.value)
    if optimizier is schemas.constants.OptimizerType.SGD:
        return torch.optim.SGD(params, lr=lr, momentum=momentum, weight_decay=weight_decay)

    if optimizier is schemas.constants.OptimizerType.RMSPROP:
        return torch.optim.RMSprop(params, lr=lr, momentum=momentum, weight_decay=weight_decay, alpha=alpha)

    if optimizier is schemas.constants.OptimizerType.ADAM:
        return torch.optim.Adam(params, lr=lr, betas=betas, weight_decay=weight_decay)

    if optimizier is schemas.constants.OptimizerType.ADAMW:
        return torch.optim.AdamW(params, lr=lr, betas=betas, weight_decay=weight_decay)


def get_scheduler(
    scheduler: schemas.constants.SchedulerType,
    optimizer: torch.optim,
    num_epochs: int,
    step_size: int = 30,
    gamma: float = 0.1,
    lr_min: float = 0.0,
) -> torch.optim.lr_scheduler:
    """
    Get scheduler for the optimizer.

    Args:
    -----
        scheduler: schemas.constants.SchedulerType
            Scheduler type.

        optimizer: torch.optim
            Optimizer to apply scheduler.

        num_epochs: int
            Number of epochs to train.

        step_size: int, optional
            Step size for the scheduler.

        gamma: float, optional
            Gamma for the scheduler.

        lr_min: float, optional
            Minimum learning rate for the scheduler.

    Returns:
    --------
        scheduler: torch.optim.lr_scheduler
            Scheduler for the optimizer.
    """

    local_logger.info("Creating scheduler: %s for optimizer.", scheduler.value)
    local_logger.info(
        "The number of epochs: %d, step_size: %d, gamma: %.4f, lr_min: %.4f",
        num_epochs,
        step_size,
        gamma,
        lr_min,
    )

    if scheduler is schemas.constants.SchedulerType.STEP:
        return torch.optim.lr_scheduler.StepLR(optimizer=optimizer, step_size=step_size, gamma=gamma)

    if scheduler is schemas.constants.SchedulerType.COSINE:
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer=optimizer, T_max=num_epochs, eta_min=lr_min)


def get_class_mapping(
    dataset: torchvision.datasets.ImageFolder,
    savepath: Optional[str],
) -> dict[str, str]:
    """
    Get class mapping from the dataset.

    Args:
    -----
        dataset: torchvision.datasets.ImageFolder
            Dataset to get class mapping.

        savepath: str, optional
            Path to save the class mapping.

    Returns:
    --------
        mapping: dict[str, str]
            Class mapping of the dataset.
    """

    mapping = dataset.class_to_idx
    local_logger.info("Reading class mapping in the dataset: %s.", mapping)

    if savepath:
        core.utils.save_as_yml(savepath, mapping)
        local_logger.info("Saved class mapping to %s.", savepath)

    return mapping
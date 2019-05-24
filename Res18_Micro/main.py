import time
import numpy as np
import argparse

import torch
import torch.nn as nn
import torch.utils.data as data
from torch.autograd import Variable

import model
import dataset
import lossfunction


if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('--train', action='store_true')
	parser.add_argument('--inference', action='store_true')
	parser.add_argument('--data_path', type=str, default='./micro')
	parser.add_argument('--ckpt_path', type=str, default='./model.tar')
	parser.add_argument('--model', type=str, default='ResNet18')
	parser.add_argument('--batch_size', type=int, default=1)
	parser.add_argument('--epoch_size', type=int, default=1)
	parser.add_argument('--optim', type=str, default='SGD')
	parser.add_argument('--loss_function', type=str, default='CrossEntropyLoss')
	args = parser.parse_args()

	if args.train:

		DATASET = dataset.Micro(args.data_path)
		DATALOADER = data.DataLoader(DATASET, batch_size=args.batch_size, shuffle=True)
		NUM_CLASSES = DATASET.num_classes
		print('Data path: ' + args.data_path)
		print('Number of classes: %d'%NUM_CLASSES)
		print('Batch size: %d'%args.batch_size)
		print('Epoch size: %d'%args.epoch_size)

		num_batches = len(DATALOADER)
		batch_total = num_batches * args.epoch_size

		MODEL = model.ResNet18(num_classes=NUM_CLASSES)
		ARCFACE = lossfunction.Arcface(512, NUM_CLASSES)
		if torch.cuda.device_count() > 1:
			MODEL = nn.DataParallel(MODEL)
			ARCFACE = nn.DataParallel(ARCFACE)
		if torch.cuda.is_available():
			MODEL.cuda()
			ARCFACE.cuda()
			print('GPU count: %d'%torch.cuda.device_count())
			print('CUDA is ready')

		if args.optim == 'Adam':
			OPTIMIZER = torch.optim.Adam(
				[{'params': MODEL.parameters()}, {'params': ARCFACE.parameters()}], lr=1e-4
				)
		elif args.optim == 'SGD':
			OPTIMIZER = torch.optim.SGD(
				[{'params': MODEL.parameters()}, {'params': ARCFACE.parameters()}], lr=1e-2, momentum=0.9
				)

		if args.loss_function == 'CrossEntropyLoss':
			LOSS = nn.CrossEntropyLoss()
		elif args.loss_function == 'FocalLoss':
			LOSS = lossfunction.FocalLoss(num_classes=NUM_CLASSES, alpha=0.25)

		MODEL.train()
		start = time.time()
		for epoch_idx in range(args.epoch_size):
			for batch_idx, (img, label) in enumerate(DATALOADER):

				img = Variable(img).cuda()
				label = Variable(label).cuda()

				OPTIMIZER.zero_grad()
				output = MODEL(img)
				output = ARCFACE(output, label)
				loss = LOSS(output, label)
				loss.backward()
				OPTIMIZER.step()

				num_corr = sum(torch.eq(torch.argmax(output, dim=1), label)).cpu().numpy()
				acc = 100 * num_corr / args.batch_size

				batch_processed = epoch_idx * num_batches + batch_idx + 1
				speed = batch_processed / (time.time() - start)
				remain_time = (batch_total - batch_processed) / speed / 3600
				print('Progress: %d/%d Loss: %f Accuracy: %.2f Remaining time: %.2f hrs'%(
					batch_processed,
					batch_total,
					loss,
					acc,
					remain_time
					))

			torch.save(MODEL.state_dict(), args.ckpt_path)

	# if args.inference:

	# 	DATASET = dataset.Micro(args.data_path)
	# 	DATALOADER = data.dataloader(DATASET, batch_size=1, shuffle=False)
	#	NUM_CLASSES = DATASET.num_classes

	#	if args.model == 'ResNet18':
	#		MODEL = model.ResNet18(num_classes=NUM_CLASSES)
	# 	MODEL.load_state_dict(torch.load(args.ckpt_path))
	# 	if torch.cuda.is_available():
	# 		MODEL.cuda()

	# 	MODEL.eval()
	# 	for batch_idx, (img, label) in enumerate(DATALOADER):

	# 			img = torch.autograd.Variable(img).cuda()
	# 			label = torch.autograd.Variable(label).cuda()
	# 			output = MODEL(data)

	# 			print('Progress: %05d/%d'%(
	# 				epoch_idx * args.epoch_size + batch_idx + 1,
	# 				num_batches * args.epoch_size
	# 				))
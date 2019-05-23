import time
import numpy as np
import argparse

import torch
import torch.nn as nn
import torch.utils.data as data

import model
import dataset

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('--train', action='store_true')
	parser.add_argument('--inference', action='store_true')
	parser.add_argument('--data_path', type=str, default='./micro')
	parser.add_argument('--ckpt_path', type=str, default='./model.tar')
	parser.add_argument('--batch_size', type=int, default=1)
	parser.add_argument('--epoch_size', type=int, default=1)
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

		MODEL = model.resnet18(num_classes=NUM_CLASSES)
		if torch.cuda.device_count() > 1:
			MODEL = nn.DataParallel(MODEL)
		if torch.cuda.is_available():
			MODEL.cuda()
			print('GPU count: %d'%torch.cuda.device_count())
			print('CUDA is ready')

		OPTIMIZER = torch.optim.Adam(MODEL.parameters(), lr=1e-4)
		LOSS = nn.CrossEntropyLoss()

		MODEL.train()
		start = time.time()
		batch_total = num_batches * args.epoch_size
		for epoch_idx in range(args.epoch_size):
			for batch_idx, (img, label) in enumerate(DATALOADER):

				img = torch.autograd.Variable(img).cuda()
				label = torch.autograd.Variable(label).cuda()

				OPTIMIZER.zero_grad()
				output = MODEL(img)
				loss = LOSS(output, label)
				loss.backward()
				OPTIMIZER.step()

				batch_processed = epoch_idx * args.epoch_size + batch_idx + 1
				speed = (time.time() - start) / batch_processed
				remain_time = (batch_total - batch_processed) * speed / 3600
				print('Progress: %05d/%05d Loss: %f Remaining time: %.2f hrs'%(
					batch_processed,
					batch_total,
					loss,
					remain_time
					))

		torch.save(MODEL.state_dict(), args.ckpt_path)

	# if args.inference:

	# 	DATASET = dataset.Micro(args.data_path)
	# 	DATALOADER = data.dataloader(DATASET, batch_size=1, shuffle=False)

	# 	MODEL = model.resnet18(num_classes=DATASET.num_classes)
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
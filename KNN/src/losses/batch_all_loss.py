import torch

class BatchAllTripletLoss:
    def __init__(self, margin=1.0):
        self.margin = margin
        self.last_positive_fraction = 0.0

    def __call__(self, labels, embeddings):
        loss, positive_fraction = self.batch_all_triplet_loss(labels, embeddings)

        self.last_positive_fraction = positive_fraction
        return loss


    def batch_all_triplet_loss(self, labels, embeddings, alfa=1.0, beta=1.0):
        embeddings = embeddings.squeeze()
        distance_matrix = torch.cdist(embeddings, embeddings)
        anchor_positive_dist = distance_matrix.unsqueeze(2)
        anchor_negative_dist = distance_matrix.unsqueeze(1)

        triplet_loss = alfa*anchor_positive_dist - beta*anchor_negative_dist + self.margin
        mask = self.create_triplet_mask(labels)
        mask = mask.float()

        triplet_loss = torch.mul(triplet_loss, mask)

        triplet_loss = torch.clamp(triplet_loss, min=0)   # element-wise max(elem, 0.00), remove negatives values
        
        num_positive_triplets = int(torch.sum(torch.where( triplet_loss > 1e-16, 1, 0))) # count number of triplets, where loss > 0, positive loss functions
        num_valid_triplets = torch.sum(mask)    # Count all triplets possible from batch 
        fraction_positive = num_positive_triplets / (num_valid_triplets + 1e-16)
        
        triplet_loss = torch.sum(triplet_loss) / (num_positive_triplets + 1e-16)
        
        return triplet_loss, fraction_positive

    def create_triplet_mask(self, labels):
        indices_equal = torch.eye(len(labels), dtype=bool)
        indices_not_equal = torch.logical_not(indices_equal)
        i_not_equal_j = indices_not_equal.unsqueeze(2)
        i_not_equal_k = indices_not_equal.unsqueeze(1)
        j_not_equal_k = indices_not_equal.unsqueeze(0)
        
        distinct_indices = torch.logical_and(torch.logical_and(i_not_equal_j, i_not_equal_k), j_not_equal_k)
        
        labels = torch.Tensor(labels)
        label_equal = torch.eq(labels.unsqueeze(0), labels.unsqueeze(1))
        i_equal_j = label_equal.unsqueeze(2)
        i_equal_k = label_equal.unsqueeze(1)

        valid_labels = torch.logical_and(i_equal_j, torch.logical_not(i_equal_k))

        # Combine the two masks
        mask = torch.logical_and(distinct_indices, valid_labels)

        return mask


class HardNegativeMiningTripletLoss:
    def __init__(self, margin) -> None:
        self.margin = margin

    def __call__(self, labels, embeddings):
        loss = self.hard_negative_batch_triplet_loss(labels, embeddings)

        return loss

    def get_positive_anchor_mask(self, labels):
        labels = torch.tensor(labels)
        indices_equal = torch.eye(len(labels), dtype=bool)
        indices_not_equal = torch.logical_not(indices_equal)

        # Check if label[i] == label[j]
        labels_equal = torch.eq(labels.unsqueeze(0), labels.unsqueeze(1))
        
        mask = torch.logical_and(indices_not_equal, labels_equal)

        return mask

    def get_negative_anchor_mask(self, labels):
        labels = torch.tensor(labels)

        labels_not_equal = torch.eq(labels.unsqueeze(0), labels.unsqueeze(1))
        mask = torch.logical_not(labels_not_equal)

        return mask

    def hard_negative_batch_triplet_loss(self, labels, embeddings):
        embeddings = embeddings.squeeze()
        distance_matrix = torch.cdist(embeddings, embeddings)
        
        # Get hardest positive for each anchor
        mask_anchor_positive = self.get_positive_anchor_mask(labels)
        mask_anchor_positive = mask_anchor_positive.float()

        # Use only distances created from positive anchors ( they have same label )
        anchor_positive_dist = torch.mul(distance_matrix, mask_anchor_positive)
        
        hardest_positive_dist, _ = torch.max(anchor_positive_dist, dim=1, keepdim=True)
        
        # Get hardest negative for each anchor
        mask_anchor_negative = self.get_negative_anchor_mask(labels)
        mask_anchor_negative = mask_anchor_negative.float()
        
        # We need to invalidate negatives for negative max ( label(a) == label(n) )
        # We get maximum distance from distance matrix and then add this max dist to every invalid negative anchor
        max_anchor_negative_dist, _ = torch.max(distance_matrix, dim=1, keepdim=True)
        anchor_negative_dist = distance_matrix + max_anchor_negative_dist * (1.0 - mask_anchor_negative) 
        
        hardest_negative_dist, _ = torch.min(anchor_negative_dist, dim=1, keepdim=True)
        
        # Calculate the triplet loss from positive and negatives hardest distances 
        triplet_loss = torch.clamp(hardest_positive_dist - hardest_negative_dist + self.margin, min=0.0)
        
        triplet_loss = torch.mean(triplet_loss)
        return triplet_loss
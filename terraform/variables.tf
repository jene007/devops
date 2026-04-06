variable "cloud_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for JARVIS VPC"
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.42.1.0/24"
}

variable "instance_count" {
  description = "Number of EC2 instances"
  type        = number
  default     = 2
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "create_eks" {
  description = "Set true to create EKS cluster"
  type        = bool
  default     = false
}

variable "eks_cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "jarvis-eks"
}

variable "eks_cluster_role_arn" {
  description = "IAM role ARN for EKS cluster"
  type        = string
  default     = ""
}

variable "eks_subnet_ids" {
  description = "Subnet IDs for EKS cluster"
  type        = list(string)
  default     = []
}

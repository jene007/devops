output "instance_public_ips" {
  description = "Public IPs of EC2 instances"
  value       = aws_instance.jarvis_node[*].public_ip
}

output "vpc_id" {
  description = "Provisioned VPC ID"
  value       = aws_vpc.jarvis_vpc.id
}

output "public_subnet_id" {
  description = "Provisioned public subnet ID"
  value       = aws_subnet.jarvis_public_subnet.id
}

output "eks_cluster_name" {
  description = "Created EKS cluster name"
  value       = try(aws_eks_cluster.jarvis_eks[0].name, null)
}

output "eks_endpoint" {
  description = "EKS API server endpoint"
  value       = try(aws_eks_cluster.jarvis_eks[0].endpoint, null)
}

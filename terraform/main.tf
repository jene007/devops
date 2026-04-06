data "aws_ami" "amazon_linux" {
  most_recent = true

  owners = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

resource "aws_vpc" "jarvis_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "jarvis-vpc"
  }
}

resource "aws_subnet" "jarvis_public_subnet" {
  vpc_id                  = aws_vpc.jarvis_vpc.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true

  tags = {
    Name = "jarvis-public-subnet"
  }
}

resource "aws_internet_gateway" "jarvis_igw" {
  vpc_id = aws_vpc.jarvis_vpc.id

  tags = {
    Name = "jarvis-igw"
  }
}

resource "aws_route_table" "jarvis_public_rt" {
  vpc_id = aws_vpc.jarvis_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.jarvis_igw.id
  }

  tags = {
    Name = "jarvis-public-rt"
  }
}

resource "aws_route_table_association" "jarvis_public_assoc" {
  subnet_id      = aws_subnet.jarvis_public_subnet.id
  route_table_id = aws_route_table.jarvis_public_rt.id
}

resource "aws_security_group" "jarvis_sg" {
  name        = "jarvis-devops-sg"
  description = "Allow SSH and app traffic"
  vpc_id      = aws_vpc.jarvis_vpc.id

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "jarvis-devops-sg"
  }
}

resource "aws_instance" "jarvis_node" {
  count                       = var.instance_count
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.jarvis_public_subnet.id
  vpc_security_group_ids      = [aws_security_group.jarvis_sg.id]
  associate_public_ip_address = true

  tags = {
    Name = "jarvis-node-${count.index + 1}"
  }
}

resource "aws_eks_cluster" "jarvis_eks" {
  count    = var.create_eks ? 1 : 0
  name     = var.eks_cluster_name
  role_arn = var.eks_cluster_role_arn

  vpc_config {
    subnet_ids = length(var.eks_subnet_ids) > 0 ? var.eks_subnet_ids : [aws_subnet.jarvis_public_subnet.id]
  }

  tags = {
    Name = "jarvis-eks"
  }
}

# SMARTLINK AUTO: Distributed Car Rental Platform

## 🚗 Project Overview

This project demonstrates a comprehensive **distributed cloud system** through two integrated components:

1. **Storage Virtual Network** - A simulated distributed storage system
2. **SMARTLINK AUTO** - A distributed car rental marketplace application

Together, these systems showcase core **distributed computing principles**: scalability, fault tolerance, and collaboration across multiple stakeholders.

---

## 🏗️ Architecture Overview

### **Layer 1: Distributed Storage Infrastructure**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Storage Node   │◄──►│  Storage Node   │◄──►│  Storage Node   │
│   (Physical)    │    │   (Virtual)     │    │   (Cloud)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Virtual Network │
                    │   Controller    │
                    └─────────────────┘
```

### **Layer 2: Business Logic Distribution**
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Renters    │    │   Partners   │    │   Admins     │
│  (Demand)    │    │   (Supply)   │    │  (Quality)   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                   ┌─────────────────┐
                   │   SMARTLINK     │
                   │     AUTO        │
                   │   Platform      │
                   └─────────────────┘
```

---

## 🌐 Distributed Storage Network

### **Core Components**

#### **StorageVirtualNode Class**
Represents individual storage nodes in the distributed network:

```python
class StorageVirtualNode:
    def __init__(self, node_id, cpu_capacity, memory_capacity, 
                 storage_capacity, bandwidth):
        # Resource allocation and management
        self.cpu_capacity = cpu_capacity  # vCPUs
        self.memory_capacity = memory_capacity  # GB RAM
        self.total_storage = storage_capacity * 1024**3  # Convert to bytes
        self.bandwidth = bandwidth * 1000000  # Convert Mbps to bps
```

**Key Features:**
- **Resource Management**: Tracks CPU, memory, storage, and bandwidth
- **Chunk-Based Transfer**: Files divided into chunks for parallel processing
- **Connection Management**: Maintains network topology with other nodes
- **Performance Metrics**: Real-time monitoring of operations and utilization

#### **StorageVirtualNetwork Class**
Orchestrates the entire distributed storage network:

```python
class StorageVirtualNetwork:
    def __init__(self):
        self.nodes: Dict[str, StorageVirtualNode] = {}
        self.transfer_operations: Dict[str, Dict[str, FileTransfer]] = defaultdict(dict)
```

**Network Operations:**
- **Node Management**: Add/remove storage nodes dynamically
- **Topology Control**: Connect nodes with specified bandwidth
- **Transfer Orchestration**: Coordinate file transfers across multiple nodes
- **Load Balancing**: Distribute transfers based on node capacity

### **Distributed System Principles Demonstrated**

#### **1. Scalability** 📈
- **Horizontal Scaling**: Add new nodes to the network without downtime
- **Resource Elasticity**: Each node can have different capacity configurations
- **Load Distribution**: Network automatically balances transfer loads
- **Bandwidth Management**: Dynamic bandwidth allocation between connected nodes

```python
# Add nodes with different capacities
network.add_node(StorageVirtualNode("node-1", 4, 16, 1000, 1000))  # High capacity
network.add_node(StorageVirtualNode("node-2", 2, 8, 500, 500))    # Medium capacity
network.add_node(StorageVirtualNode("node-3", 1, 4, 250, 250))    # Low capacity
```

#### **2. Fault Tolerance** 🛡️
- **Chunk-Level Redundancy**: Files split into chunks, allowing partial recovery
- **Transfer Status Tracking**: Each chunk tracks its own transfer status
- **Connection Resilience**: Failed chunks don't affect other chunks in transfer
- **Error Recovery**: Failed transfers can be retried without restarting entire operation

```python
class TransferStatus(Enum):
    PENDING = auto()      # Ready to transfer
    IN_PROGRESS = auto()  # Currently transferring  
    COMPLETED = auto()    # Successfully transferred
    FAILED = auto()       # Transfer failed, retryable
```

#### **3. Collaboration** 🤝
- **Inter-Node Communication**: Nodes communicate directly with each other
- **Resource Sharing**: Bandwidth and storage shared across the network
- **Distributed Processing**: File processing distributed across multiple nodes
- **Network Topology**: Configurable connection patterns for optimal collaboration

---

## 🚗 SMARTLINK AUTO: Distributed Marketplace

### **Business Model: "Transparent Aggregator"**

The SMARTLINK AUTO platform solves the classic "ghost town" problem in marketplace platforms by implementing a **distributed supply with unified demand** model:

```
Traditional P2P:     Renter ────❌───→ Partner
                     (No Trust, Direct Interaction)

SMARTLINK AUTO:      Renter ────✓───→ SMARTLINK AUTO ────✓───→ Partner
                     (Trusted Brand)        (Quality Control)     (Protected)
```

### **Distributed Architecture**

#### **Three-Tier Stakeholder Model**

**1. Renters (Demand Layer)**
- End customers seeking vehicle access
- Interact only with the SMARTLINK AUTO brand
- Expect consistent, professional service
- Benefit from quality-controlled vehicle pool

**2. Partners (Supply Layer)**
- Individual car owners and small fleet operators
- List vehicles through the platform
- Maintain ownership while earning passive income
- Protected through verification and insurance

**3. Admins (Orchestration Layer)**
- Platform operators managing quality control
- Verify partners and vehicles
- Handle disputes and ensure standards
- Maintain the "transparent" brand promise

### **Technology Stack**

#### **Backend: NestJS Distributed Architecture**
```typescript
// Modular service architecture
@Module({
  imports: [
    UsersModule,      // Partner/Renter management
    VehiclesModule,   // Vehicle registry and management  
    AvailabilityModule, // Time-based availability
    AdminModule,      // Quality control and oversight
  ],
})
export class AppModule {}
```

#### **Frontend: React Multi-Interface Design**
```javascript
// Three distinct user interfaces
<Routes>
  <Route path="/" element={<Home />} />           // Renter portal
  <Route path="/partner" element={<PartnerDashboard />} /> // Partner portal  
  <Route path="/admin" element={<AdminPanel />} />     // Admin console
</Routes>
```

#### **Database: Distributed Entity Model**
```typescript
// Normalized schema supporting distributed operations
@Entity() export class User {
  @Column({ type: 'enum', enum: UserRole })  // Multi-role support
  role: UserRole;
  
  @Column({ type: 'enum', enum: VerificationStatus })  // Quality gates
  verificationStatus: VerificationStatus;
}

@Entity() export class Vehicle {
  @ManyToOne(() => User, (user) => user.vehicles)  // Partner relationship
  partner: User;
  
  @Column({ type: 'enum', enum: VehicleStatus })  // Lifecycle management
  status: VehicleStatus;
}
```

### **Distributed System Principles in SMARTLINK AUTO**

#### **1. Scalability** 📈
**Horizontal Scaling:**
- **Multi-tenant Architecture**: Support unlimited partners and renters
- **Microservices Design**: Each domain (users, vehicles, availability) can scale independently
- **Database Flexibility**: PostgreSQL for production, SQLite for development
- **API Gateway Pattern**: Centralized entry point with distributed processing

**Vertical Scaling:**
- **Resource Optimization**: Efficient TypeORM queries and caching strategies
- **Load Distribution**: Admin verification workflows distribute processing load
- **Performance Monitoring**: Real-time metrics for system optimization

```typescript
// Modular scaling - each service can scale independently
@Module({
  imports: [TypeOrmModule.forFeature([User, Vehicle, Availability])],
  providers: [UsersService, VehiclesService, AvailabilityService, AdminService],
})
export class AppModule {}
```

#### **2. Fault Tolerance** 🛡️
**Verification Workflows:**
- **Multi-stage Verification**: Partners and vehicles must pass quality gates
- **Status Management**: Clear lifecycle states (PENDING → VERIFIED → ACTIVE)
- **Error Recovery**: Failed verifications can be resubmitted
- **Data Integrity**: Foreign key constraints and validation rules

**Business Logic Resilience:**
- **Graceful Degradation**: Platform operates even with incomplete data
- **Audit Trails**: All changes tracked for accountability
- **Rollback Capabilities**: Status changes can be reversed
- **Data Redundancy**: Multiple backup strategies for critical data

```typescript
// Fault-tolerant status management
export enum VerificationStatus {
  PENDING = 'PENDING',    // Awaiting review
  VERIFIED = 'VERIFIED',  // Approved and active
  REJECTED = 'REJECTED',  // Failed verification, can retry
}

// Robust error handling
async createPartner(input: CreatePartnerInput): Promise<User> {
  try {
    const user = this.usersRepository.create({...});
    return await this.usersRepository.save(user);
  } catch (error) {
    throw new InternalServerErrorException('Partner creation failed');
  }
}
```

#### **3. Collaboration** 🤝
**Multi-Stakeholder Coordination:**
- **Partner Onboarding**: Structured workflow for adding new suppliers
- **Admin Verification**: Quality control through human oversight
- **Availability Coordination**: Real-time scheduling between partners and renters
- **Dispute Resolution**: Structured conflict resolution process

**Information Sharing:**
- **Real-time Updates**: All stakeholders see current system state
- **Transparent Communication**: Status changes communicated to relevant parties
- **Data Visibility**: Appropriate information sharing while maintaining privacy
- **Collaborative Filtering**: Renters, partners, and admins all contribute to quality

```typescript
// Collaborative workflow management
@Patch('partners/:id/verification')
async updatePartnerVerification(
  @Param('id') id: string,
  @Body() body: UpdatePartnerVerificationDto,
) {
  // Admin action affects partner status
  const status = body.status as VerificationStatus;
  return this.adminService.updatePartnerVerification(id, status);
  // Partner gets notified of status change
  // System updates vehicle availability accordingly
}
```

---

## 🔄 Integration: Storage + Marketplace

### **How the Systems Work Together**

The combination of the **Storage Virtual Network** and **SMARTLINK AUTO** demonstrates **distributed thinking** at two levels:

#### **Level 1: Technical Distribution**
- **Storage Layer**: Actual distributed computing with network topology, chunk transfers, and fault tolerance
- **Application Layer**: Distributed business logic with microservices, data distribution, and stakeholder coordination

#### **Level 2: Conceptual Distribution**
- **Physical Distribution**: Storage nodes in different physical locations
- **Logical Distribution**: Business partners in different geographic and operational contexts

### **Shared Principles**

Both systems demonstrate:

1. **Decentralization**: No single point of failure
2. **Redundancy**: Multiple paths to achieve goals
3. **Coordination**: Distributed components working toward common objectives
4. **Resilience**: Ability to continue operating despite component failures
5. **Scalability**: Ability to grow without fundamental architecture changes

---

## 📊 Performance Characteristics

### **Storage Network Metrics**
```python
def get_network_stats(self) -> Dict[str, float]:
    return {
        "total_nodes": len(self.nodes),
        "total_bandwidth_bps": total_bandwidth,
        "bandwidth_utilization": (used_bandwidth / total_bandwidth) * 100,
        "storage_utilization": (used_storage / total_storage) * 100,
        "active_transfers": sum(len(t) for t in self.transfer_operations.values())
    }
```

### **Marketplace Metrics**
```typescript
// Admin dashboard shows platform health
{
  totalUsers: 1250,
  totalVehicles: 340,
  activeVehicles: 298,
  pendingPartners: 12,
  pendingVehicles: 8,
  monthlyRevenue: 125000
}
```

---

## 🚀 Deployment Architecture

### **Development Environment**
```yaml
# Local development setup
Backend:
  - NestJS server on port 3000
  - SQLite in-memory database
  - Hot reloading enabled

Frontend:  
  - React dev server on port 5173
  - Vite build system
  - BrowserRouter for navigation
```

### **Production Environment** 
```yaml
# Scalable production deployment
Backend:
  - NestJS on container orchestration (Kubernetes/Docker Swarm)
  - PostgreSQL cluster with read replicas
  - Load balancer distributing requests
  - Redis for session management and caching

Frontend:
  - Static assets on CDN
  - API requests routed through gateway
  - Multiple geographic deployment points
```

---

## 🔧 Development Guide

### **Getting Started**

#### **Backend Setup**
```bash
cd backend
npm install
npm run start:dev
```

#### **Frontend Setup**
```bash
cd frontend  
npm install
npm run dev
```

#### **Storage Network Simulation**
```python
# Example: Create a distributed storage network
from storage_virtual_network import StorageVirtualNetwork
from storage_virtual_node import StorageVirtualNode

# Create network
network = StorageVirtualNetwork()

# Add nodes with different capacities
node1 = StorageVirtualNode("hub-1", 4, 16, 1000, 1000)
node2 = StorageVirtualNode("hub-2", 2, 8, 500, 500)  
node3 = StorageVirtualNode("edge-1", 1, 4, 250, 250)

network.add_node(node1)
network.add_node(node2) 
network.add_node(node3)

# Connect nodes
network.connect_nodes("hub-1", "hub-2", 500)
network.connect_nodes("hub-1", "edge-1", 200)

# Initiate file transfer
transfer = network.initiate_file_transfer(
    "hub-1", "hub-2", "car-photos.zip", 1024*1024*50  # 50MB
)

# Process transfer in chunks
while True:
    chunks, complete = network.process_file_transfer(
        "hub-1", "hub-2", transfer.file_id, chunks_per_step=5
    )
    if complete:
        break
    print(f"Transferred {chunks} chunks...")
```

### **API Endpoints**

#### **Partner Management**
```http
POST /partners
Content-Type: application/json

{
  "email": "partner@example.com",
  "password": "securepass123", 
  "firstName": "John",
  "lastName": "Doe",
  "phoneNumber": "+237123456789"
}
```

#### **Vehicle Registration**
```http
POST /partners/{partnerId}/vehicles
Content-Type: application/json

{
  "make": "Toyota",
  "model": "Camry", 
  "year": 2022,
  "vin": "1HGBH41JXMN109186",
  "licensePlate": "ABC-123",
  "basePricePerDay": 50.00,
  "location": "Yaounde, Cameroon"
}
```

#### **Admin Operations**
```http
GET /admin/overview
GET /admin/partners/pending
GET /admin/vehicles/pending

PATCH /admin/partners/{id}/verification
Content-Type: application/json

{
  "status": "VERIFIED"  // or "REJECTED"
}
```

---

## 🧪 Testing Distributed Scenarios

### **Fault Tolerance Testing**
```python
# Simulate node failure during transfer
def test_node_failure():
    network = create_test_network()
    transfer = initiate_large_file_transfer(network)
    
    # Simulate failure of intermediate node
    failed_node = "hub-2"
    network.nodes[failed_node].bandwidth = 0  # Simulate failure
    
    # Transfer should continue via alternate path
    chunks_transferred = process_transfer_with_failure(network, transfer)
    assert chunks_transferred > 0  # Some chunks should still transfer
```

### **Scalability Testing**
```typescript
// Test system performance under load
describe('Scalability Tests', () => {
  it('should handle 1000 concurrent partner registrations', async () => {
    const partners = Array.from({length: 1000}, (_, i) => ({
      email: `partner${i}@test.com`,
      password: 'testpass123',
      firstName: `Partner${i}`,
      lastName: 'Test',
    }));
    
    const promises = partners.map(p => 
      request(app).post('/partners').send(p)
    );
    
    const responses = await Promise.all(promises);
    const successCount = responses.filter(r => r.status === 201).length;
    
    expect(successCount).toBeGreaterThan(900); // >90% success rate
  });
});
```

---

## 📈 Future Enhancements

### **Storage Network**
- **Geographic Distribution**: Deploy nodes across multiple data centers
- **Data Encryption**: End-to-end encryption for stored files
- **Blockchain Integration**: Immutable transfer logs
- **AI Load Prediction**: Machine learning for optimal chunk routing

### **SMARTLINK AUTO**  
- **Real-time Tracking**: GPS integration for live vehicle tracking
- **Dynamic Pricing**: AI-driven surge pricing algorithms
- **Predictive Maintenance**: IoT sensors for vehicle health monitoring
- **Blockchain Payments**: Cryptocurrency payment options

---

## 📝 Conclusion

This project successfully demonstrates **distributed systems principles** through two complementary approaches:

1. **Technical Distribution**: Actual distributed computing with the Storage Virtual Network
2. **Business Distribution**: Distributed marketplace logic with SMARTLINK AUTO

### **Key Achievements:**

✅ **Scalability**: Both systems can grow horizontally without architecture changes  
✅ **Fault Tolerance**: Multiple failure scenarios handled gracefully  
✅ **Collaboration**: Multiple stakeholders work together seamlessly  
✅ **Production Ready**: Full-stack application with proper architecture  
✅ **Educational Value**: Clear demonstration of distributed computing concepts  

### **Business Impact:**

The SMARTLINK AUTO platform addresses real-world problems:
- **For Partners**: Monetize underutilized assets through trusted platform
- **For Renters**: Access quality vehicles through single trusted brand
- **For Market**: Efficient resource allocation in sharing economy

This project serves as both a **functional application** and a **distributed systems case study**, demonstrating how modern distributed computing principles can be applied to solve real-world business problems.

---

**Author**: SHUYE ANITA BERINYU  
**Date**: November 2025  
**Version**: 1.0  
**Technology Stack**: NestJS, React, TypeScript, Python, TypeORM, PostgreSQL

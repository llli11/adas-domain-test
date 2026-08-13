-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: 10.82.77.87    Database: mydb_local
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tool_borrow`
--

DROP TABLE IF EXISTS `tool_borrow`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tool_borrow` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `tool_id` int NOT NULL COMMENT '工具ID',
  `tool_code` varchar(100) NOT NULL COMMENT '工具编码',
  `tool_name` varchar(100) NOT NULL COMMENT '工具名称',
  `borrower_id` int NOT NULL COMMENT '借用人ID',
  `borrower_name` varchar(50) NOT NULL COMMENT '借用人姓名',
  `borrow_date` datetime(6) NOT NULL COMMENT '借用时间',
  `expected_return_date` datetime(6) DEFAULT NULL COMMENT '预计归还时间',
  `actual_return_date` datetime(6) DEFAULT NULL COMMENT '实际归还时间',
  `status` varchar(20) NOT NULL DEFAULT '借用中' COMMENT '状态: 借用中/已归还/逾期',
  `purpose` varchar(200) DEFAULT NULL COMMENT '借用用途',
  `approver_id` int DEFAULT NULL COMMENT '审批人ID',
  `approver_name` varchar(50) DEFAULT NULL COMMENT '审批人姓名',
  `approve_status` varchar(20) NOT NULL DEFAULT '待审批' COMMENT '审批状态: 待审批/已通过/已拒绝',
  `approve_time` datetime(6) DEFAULT NULL COMMENT '审批时间',
  `remark` longtext COMMENT '备注',
  PRIMARY KEY (`id`),
  KEY `idx_tool_borrow_created_c29b87` (`created_at`),
  KEY `idx_tool_borrow_updated_586978` (`updated_at`),
  KEY `idx_tool_borrow_tool_id_f5e320` (`tool_id`),
  KEY `idx_tool_borrow_tool_co_a08387` (`tool_code`),
  KEY `idx_tool_borrow_borrowe_c80acf` (`borrower_id`),
  KEY `idx_tool_borrow_borrowe_b2d900` (`borrower_name`),
  KEY `idx_tool_borrow_borrow__67e8fa` (`borrow_date`),
  KEY `idx_tool_borrow_status_e84879` (`status`),
  KEY `idx_tool_borrow_approve_db3603` (`approve_status`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tool_borrow`
--

LOCK TABLES `tool_borrow` WRITE;
/*!40000 ALTER TABLE `tool_borrow` DISABLE KEYS */;
INSERT INTO `tool_borrow` VALUES (1,'2026-07-08 17:14:11.671188','2026-07-08 17:14:14.733779',1,'111111111','1111111111',1,'','2026-07-08 17:14:11.507000',NULL,NULL,'借用中','',1,'admin','已拒绝','2026-07-08 09:14:14.732034','');
/*!40000 ALTER TABLE `tool_borrow` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:50

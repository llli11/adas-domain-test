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
-- Table structure for table `contractor_staff`
--

DROP TABLE IF EXISTS `contractor_staff`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contractor_staff` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  `name` varchar(20) NOT NULL COMMENT '姓名',
  `type` varchar(20) DEFAULT NULL COMMENT '属性（工程师/驾驶员）',
  `gender` varchar(10) DEFAULT NULL COMMENT '性别',
  `id_card` varchar(18) DEFAULT NULL COMMENT '身份证号',
  `phone` varchar(20) DEFAULT NULL COMMENT '电话号码',
  `company` varchar(100) DEFAULT NULL COMMENT '公司',
  `position` varchar(50) DEFAULT NULL COMMENT '岗位',
  `project_id` int DEFAULT NULL COMMENT '所属项目',
  `responsible_user_id` int DEFAULT NULL COMMENT '责任人（关联user）',
  `entry_date` datetime(6) DEFAULT NULL COMMENT '入职时间',
  `resignation_date` datetime(6) DEFAULT NULL COMMENT '离职时间',
  `status` varchar(20) NOT NULL DEFAULT '在职' COMMENT '状态（在职/离职中/离职）',
  `current_task` varchar(50) DEFAULT NULL COMMENT '当前任务（泊车/行车/LO/L1）',
  `current_vehicle` varchar(50) DEFAULT NULL COMMENT '当前所在车辆',
  `task_status` varchar(20) NOT NULL DEFAULT '空闲' COMMENT '任务状态（空闲/任务中）',
  `is_idle` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否空闲',
  `resignation_id` int DEFAULT NULL COMMENT '关联离职记录ID',
  `remark` longtext COMMENT '备注',
  PRIMARY KEY (`id`),
  KEY `idx_contractor__created_1ef915` (`created_at`),
  KEY `idx_contractor__updated_83896b` (`updated_at`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='外委人员信息表（人力台账）';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contractor_staff`
--

LOCK TABLES `contractor_staff` WRITE;
/*!40000 ALTER TABLE `contractor_staff` DISABLE KEYS */;
/*!40000 ALTER TABLE `contractor_staff` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-13 10:15:51

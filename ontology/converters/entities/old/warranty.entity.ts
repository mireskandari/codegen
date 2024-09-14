import { EventPublisher } from '@nestjs/cqrs';
import { VsolvEntity } from '@vsolv/dev-kit/nest';
import { AssetEntity } from '@wsphere/assets/api';
import { CustomerEntity } from '@wsphere/customers/api';
import { Warranty } from '@wsphere/warranties/domain';
import {
  Column,
  CreateDateColumn,
  JoinColumn,
  ManyToOne,
  PrimaryColumn,
  TableInheritance,
  UpdateDateColumn,
} from 'typeorm';
import { PolicyEntity } from '../../policy';
import { WarrantyAggregate } from '../models';

@TableInheritance({ column: 'type' })
@VsolvEntity({ prefix: 'wrt', name: 'warranty' }, 'tenant')
export abstract class WarrantyEntity<T extends string> {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true, unique: true })
  referenceId!: string | null;

  @Column({ type: 'simple-enum', enum: Warranty.Status })
  status!: Warranty.Status;

  @Column()
  type!: T;

  @CreateDateColumn()
  created!: Date;

  @UpdateDateColumn()
  modified!: Date;

  @Column()
  contractNumber!: string;

  @Column()
  termStart!: Date;

  @Column()
  termDuration!: number;

  @Column()
  policyId!: string;

  @JoinColumn({ name: 'policyId' })
  @ManyToOne(() => PolicyEntity)
  policy?: PolicyEntity;

  @Column()
  customerId!: string;

  @JoinColumn({ name: 'customerId' })
  @ManyToOne(() => CustomerEntity)
  customer?: CustomerEntity;

  @Column()
  assetId!: string;

  @JoinColumn({ name: 'assetId' })
  @ManyToOne(() => AssetEntity)
  asset?: AssetEntity<string>;

  abstract toAggregate(publisher?: EventPublisher): WarrantyAggregate<T>;
}

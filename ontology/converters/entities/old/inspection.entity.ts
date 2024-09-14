import { EventPublisher } from '@nestjs/cqrs';
import { VsolvEntity } from '@vsolv/dev-kit/nest';
import { AssetEntity } from '@wsphere/assets/api';
import { CustomerEntity } from '@wsphere/customers/api';
import { Inspection } from '@wsphere/inspections/domain';
import { Column, JoinColumn, ManyToOne, PrimaryColumn, TableInheritance } from 'typeorm';
import { InspectorEntity } from '../../inspector';
import { InspectionAggregate } from '../models';

@TableInheritance({ column: 'type' })
@VsolvEntity({ prefix: 'insp', name: 'inspection' }, ['tenant'])
export abstract class InspectionEntity<T extends string> implements Inspection.Model<T> {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true, unique: true })
  referenceId!: string | null;

  @Column()
  type!: T;

  @Column()
  timestamp!: Date;

  @Column()
  inspectorId!: string;

  @JoinColumn({ name: 'inspectorId' })
  @ManyToOne(() => InspectorEntity)
  inspector?: InspectorEntity;

  @Column()
  customerId!: string;

  @JoinColumn({ name: 'customerId' })
  @ManyToOne(() => CustomerEntity)
  customer?: CustomerEntity;

  @Column()
  assetId!: string;

  @JoinColumn({ name: 'assetId' })
  @ManyToOne(() => AssetEntity)
  abstract asset?: AssetEntity<string>;

  abstract toAggregate(publisher?: EventPublisher): InspectionAggregate<T>;
}

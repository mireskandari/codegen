import { EventPublisher } from '@nestjs/cqrs';
import { VsolvEntity } from '@vsolv/dev-kit/nest';
import { Asset } from '@wsphere/assets/domain';
import { Column, PrimaryColumn, TableInheritance } from 'typeorm';
import { AssetAggregate } from '../models';

@VsolvEntity({ prefix: 'ast', name: 'asset' }, ['tenant'])
@TableInheritance({ column: 'type' })
export abstract class AssetEntity<T extends string> implements Asset.Model<T> {
  @PrimaryColumn()
  id!: string;

  @Column({ nullable: true, unique: true })
  referenceId!: string | null;

  @Column()
  type!: T;

  @Column()
  name!: string;

  @Column({ type: 'longtext', nullable: true })
  description!: string | null;

  abstract toAggregate(publisher?: EventPublisher): AssetAggregate<T>;
}
